#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import os
import urlparse, urllib
import json
import urllib2
import threading
from flask import request
from flask import jsonify

from flask import Flask
app = Flask(__name__)

def post(url, payload):
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')

    return urllib2.urlopen(req, json.dumps(payload))

def login(driver, username, password, token):
    driver.get("https://rewardzone.redhat.com")
    driver.find_element_by_name("j_username").send_keys(username)
    password_obj = driver.find_element_by_name("j_password")
    password_obj.send_keys("%s%s" % (password, token))
    password_obj.submit()

def select_person(driver, email):
    driver.implicitly_wait(10) # seconds
    driver.get("https://rewardzone.redhat.com/nominations/wizardStep1/family_id/275")
    driver.implicitly_wait(10) # seconds

    driver.find_element_by_name("ams_fieldval_input").send_keys(email)

    members_list = Select(driver.find_element_by_id("available_members"))
    for x in xrange(0, 10):
        if len(members_list.options) > 0:
            break
        driver.implicitly_wait(1)
    members_list.select_by_index(0)

    driver.find_element_by_class_name("arrow_down").click()
    driver.find_element_by_name("commit").submit()

def select_reward(driver):
    driver.find_element(By.XPATH, '//a[@rel="2228"]').click()
    driver.find_element_by_name("commit").submit()

def select_points(driver, points):
    driver.find_element_by_id("pointValue").send_keys("%s" % points)
    driver.find_element_by_name("commit").submit()
    driver.implicitly_wait(10) # seconds

def select_additional_details(driver, description, message, submit=True):
    driver.find_element_by_id("achievement_description").send_keys(description)
    driver.find_element_by_id("emailmessage").send_keys(message)
    if submit:
        driver.find_element_by_name("commit").submit()

def get_driver():
    #driver = webdriver.Firefox()
    cwd = os.path.dirname(os.path.realpath(__file__))
    path_linux = os.path.join(cwd, 'bin/phantomjs')
    path_mac = os.path.join(cwd, './phantomjs_mac')
    kwargs = {
        'service_log_path': os.path.devnull,
    }

    if os.path.isfile(path_mac):
        kwargs['executable_path'] = path_mac
    else:
        kwargs['executable_path'] = path_linux

    driver = webdriver.PhantomJS(**kwargs)
    return driver

def _send_reward(response_url, rewardee, token, username, password, points, message, submit):

    try:
        post(response_url, {'text': "Started your request ..."})
        driver = get_driver()
        login(driver, username, password, token)
        select_person(driver, rewardee)
        post(response_url, {'text': "Logged in successfully ..."})
        select_reward(driver)
        select_points(driver, points)
        select_additional_details(driver, message, message, submit=submit)
        post(response_url, {'text': "Complete, %s now has +%s points!" % (rewardee, points)})
    except Exception as e:
        post(response_url, {'text': "Error ARRRR. Double check ye credentials and PIN. Ye be needing to have enough booty in ye treasure chest too.\n\n\n\n%s" % str(e)})
        post(response_url, {'text': str(e)})
    finally:
        driver.close()

@app.route("/rewardzone/reward", methods=['POST'])
def send_reward():
    rewardee = 'cmeyers@redhat.com'

    # TODO: allow spaces in the message
    x = request.form['text'].split()
    username = x[0]
    password = x[1]
    token = x[2]
    points = x[3]
    message = x[4:]
    response_url = request.form['response_url']

    submit = True
    errors = []
    if not token:
        errors.append("token not found")
    if not username:
        errors.append("username not found")
    if not password:
        errors.append("password not found")
    if not points:
        errors.append("points not found")
    if not message:
        errors.append("message not found")
    if len(errors) > 0:
        return jsonify(errors=errors)

    t = threading.Thread(target=_send_reward, args=(response_url, rewardee, token, username, password, points, message, submit))
    t.start()
    msg = 'Queued your request for %s point to be given to Chris Meyers!' % (points)
    return jsonify(text=msg)

if __name__ == "__main__":
    #app.debug = True
    app.run(host='0.0.0.0')
