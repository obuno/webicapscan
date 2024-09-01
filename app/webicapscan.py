import csv
import os
import flask
import glob
import pandas as pd
import secrets
import shutil
import subprocess
import time

from flask import Flask, flash, render_template, request, redirect, url_for, abort, send_from_directory
from werkzeug.utils import secure_filename

app = flask.Flask(__name__)

app.config["SECRET_KEY"] = str(secrets.SystemRandom().getrandbits(128))
app.config['UPLOAD_PATH_SAMPLES'] = '_to_scan'
app.config['INIT_PATH'] = '_init'
app.config['USER_ICAP_CONFIGS'] = '_icap_conf/userconfs'

revisions = "Revision: Version 0.99"
infotext1 = "ICAP Configuration	: Address/Configure your own ICAP/AV Server (Layer3). An ICAP/ClamAV combo is running on this container per default."
infotext2 = "BROWSE : Upload any contents/files to be scanned either by the local (default) or your own ICAP/AV Server, results will be shown below."
infotext3 = ""
aboutext1 = "This tool has been developed by Obuno -- you can send feedback/bug reports etc here --> obuno@protonmail.com"
configtext1 = "Please insert here your own network reachable ICAP Server Configuration Settings below or load any previously saved configuration."

@app.errorhandler(400)
def page_not_found(error):
    #error handling on untolerated uploads
    return render_template('400.html'), 400


@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():

        #ICAP config init to defaults
        src_dir = '_icap_conf_def'
        dst_dir = '_icap_conf'

        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)

        for item in os.listdir(src_dir):
            s = os.path.join(src_dir, item)
            d = os.path.join(dst_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        icapUserConfigs = os.listdir(app.config['USER_ICAP_CONFIGS'])
        icapUserConfigs = [f for f in icapUserConfigs if f.endswith(".csv")]

        return render_template('index.html', icapUserConfigs=icapUserConfigs, revisions=revisions, infotext1=infotext1, infotext2=infotext2, infotext3=infotext3, configtext1=configtext1,)


@app.route('/uploads', methods=['POST'])
def upload_sample():

    try:
        with open('_icap_conf/icapConfig.csv') as f:
            pass

    except FileNotFoundError:
        return ('Please fill-in your ICAP runtime configuration first !!!')

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    fieldnames = ['f_icapConfigName', 'f_icapServer', 'f_icapPort', 'f_icapService']
    icapCSV = pd.read_csv("_icap_conf/icapConfig.csv", usecols = ['f_icapConfigName','f_icapServer','f_icapPort','f_icapService'], header=0)
    icapProperties = list (icapCSV.values)

    icapConfigName = icapProperties[0][0]
    icapServer = icapProperties[0][1]
    icapPort = icapProperties[0][2]
    icapService = icapProperties[0][3]

    if icapService == 'default':
        return ('Please fill-in your ICAP runtime configuration first !!!')

    if filename != '':

        if os.path.isfile(os.path.join(app.config['UPLOAD_PATH_SAMPLES'], 'scan-output.txt')):
            os.remove(os.path.join(app.config['UPLOAD_PATH_SAMPLES'], 'scan-output.txt'))

        file_ext = os.path.splitext(filename)[1]
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH_SAMPLES'], filename))

        icapscan = '/opt/c-icap/bin/c-icap-client -i ' +  str(icapServer) + ' -p ' + str(icapPort) + ' -s ' + str(icapService) + ' -resp ' + str(filename) + ' -hx "Host: webicapclient" -nopreview -v -d 10 -f _to_scan/' + str(filename) + ' -o _to_scan/scan-output.txt'

        print(icapscan)

        def scan(filename):

                proc = subprocess.Popen(
                    icapscan,
                    universal_newlines=True,
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                try:
                    for line in iter(proc.stdout.readline, ''):
                        if 'status:204' in line:
                            yield line.rstrip() + '<b><br/>\n'
                            pass
                        elif 'X-Virus-ID' in line:
                            yield line.rstrip() + '<b><br/>\n'
                            pass
                        else:
                            yield line.rstrip() + '</b><br/>\n'


                except UnicodeDecodeError:
                    print("\n** Output has invalid (non utf-8) characters! Invalid output in STDOUT **\n")
                    pass

                try:
                    for line in iter(proc.stderr.readline, ''):
                        if 'status:204' in line:
                            yield line.rstrip() + '<b><br/>\n'
                            pass
                        elif 'X-Virus-ID' in line:
                            yield line.rstrip() + '<b><br/>\n'
                            pass
                        else:
                            yield line.rstrip() + '</b><br/>\n'

                except UnicodeDecodeError:
                    print("\n** Output has invalid (non utf-8) characters! Invalid output in STDERR **\n")
                    pass

                os.remove(os.path.join(app.config['UPLOAD_PATH_SAMPLES'], filename))

        # return the contents of the ICAP scan (iFrame)
        return flask.Response(scan(filename), mimetype='text/html')


@app.route('/icapconfig', methods=['POST', 'GET'])

def icapconfig():

    if request.method == 'GET':

        try:
            with open('_icap_conf/icapConfig.csv') as f:
                pass

        except FileNotFoundError:
            return render_template('icapconfig.html', configtext1=configtext1)

        icapUserConfigs = os.listdir(app.config['USER_ICAP_CONFIGS'])
        icapUserConfigs = [f for f in icapUserConfigs if f.endswith(".csv")]

        fieldnames = ['f_icapConfigName', 'f_icapServer', 'f_icapPort', 'f_icapService']
        icapCSV = pd.read_csv("_icap_conf/icapConfig.csv", usecols = ['f_icapConfigName','f_icapServer','f_icapPort','f_icapService'], header=0)
        icapProperties = list (icapCSV.values)

        icapConfigName = icapProperties[0][0]
        icapServer = icapProperties[0][1]
        icapPort = icapProperties[0][2]
        icapService = icapProperties[0][3]

        flash(('ICAP Config Name --: [ ') +str(icapConfigName) +(' ]'))
        flash(('ICAP server IP ----: [ ') +str(icapServer) +(' ]'))
        flash(('ICAP port ---------: [ ') +str(icapPort) +(' ]'))
        flash(('ICAP service ------: [ ') +str(icapService) +(' ]'))

        return render_template('icapconfig.html', configtext1=configtext1, icapUserConfigs=icapUserConfigs)

    if request.method == 'POST':

        print(request.args.get("loadUserConfig"))
        print ("POST entry 174")

        if 'loadUserConfig' in request.args:

            icapUserConfigs = os.listdir(app.config['USER_ICAP_CONFIGS'])
            icapUserConfigs = [f for f in icapUserConfigs if f.endswith(".csv")]

            loadUserConfig = request.args.get("loadUserConfig")
            loadUserConfig = str("_icap_conf/userconfs/") + loadUserConfig

            fieldnames = ['f_icapConfigName', 'f_icapServer', 'f_icapPort', 'f_icapService']
            icapCSV = pd.read_csv(loadUserConfig, usecols = ['f_icapConfigName','f_icapServer','f_icapPort','f_icapService'], header=0)
            icapProperties = list (icapCSV.values)

            icapConfigName = icapProperties[0][0]
            icapServer = icapProperties[0][1]
            icapPort = icapProperties[0][2]
            icapService = icapProperties[0][3]

            with open('_icap_conf/icapConfig.csv','w') as inFile:
                writer = csv.DictWriter(inFile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({'f_icapConfigName': icapConfigName, 'f_icapServer': icapServer, 'f_icapPort': icapPort, 'f_icapService': icapService})

            flash(('ICAP Config Name --: [ ') +str(icapConfigName) +(' ]'))
            flash(('ICAP server IP ----: [ ') +str(icapServer) +(' ]'))
            flash(('ICAP port ---------: [ ') +str(icapPort) +(' ]'))
            flash(('ICAP service ------: [ ') +str(icapService) +(' ]'))

            return render_template('icapconfig.html', configtext1=configtext1, icapUserConfigs=icapUserConfigs)

        else:

            form_data = request.form
            icapConfigName = request.form['icapConfigName']
            icapServer = request.form['icapServer']
            icapPort = request.form['icapPort']
            icapService = request.form['icapService']

            fieldnames = ['f_icapConfigName', 'f_icapServer', 'f_icapPort', 'f_icapService']

            with open('_icap_conf/icapConfig.csv','w') as inFile:
                writer = csv.DictWriter(inFile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({'f_icapConfigName': icapConfigName, 'f_icapServer': icapServer, 'f_icapPort': icapPort, 'f_icapService': icapService})

            with open('_icap_conf/userconfs/' +str(icapConfigName) + '.csv','w') as inFile:
                writer = csv.DictWriter(inFile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({'f_icapConfigName': icapConfigName, 'f_icapServer': icapServer, 'f_icapPort': icapPort, 'f_icapService': icapService})

            flash(('ICAP config [ ') +str(icapConfigName) +(' ] saved'))
            return redirect(url_for('icapconfig'))


@app.route('/about')
def about():
    return render_template('about.html', aboutext1=aboutext1)

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')
