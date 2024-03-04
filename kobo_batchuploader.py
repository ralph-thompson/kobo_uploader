#kobo_batchuploader.py
#tested on python 3.11.4 / windows 10.

import io
import requests
import uuid
from datetime import datetime
from upload_config import *
from pathlib import Path
import math
from time import sleep
#import lxml.etree as etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import traceback
import re
import os

def format_openrosa_datetime():
    return datetime.now().isoformat('T', 'milliseconds')

def create_xml_submission(_uuid, csv_dict, xml_template):
    uid = FORM_UID
    head = f'''
    <{uid} id="{uid}" version="1 (2021-03-25 18:06:48)">
        <formhub>
            <uuid>d0f06b3a0cce4a4f9c69de7fb6c10f20</uuid>
        </formhub> 
    '''
    

    body = str(xml_template) % csv_dict

    foot = f'''
        <__version__>vWG8dR5D2BhooJjhQ8zrqy</__version__>
        <meta>
            <instanceID>uuid:{_uuid}</instanceID>
        </meta>
    </{uid}>
    '''
    

    
    xml_payload = (head+body+foot)

    return xml_payload.encode()

def submit_data(i, csv_dict, csv_header, xml_template, image_dict, missing_images, number_skipped):
    try:
        _uuid = csv_dict["_uuid"]
    except:
        _uuid = str(uuid.uuid4())

    #skip submissions that miss images, if option is set
    if missing_images > 0 and SUBMIT_WITH_MISSING_IMAGES == False:
        number_skipped = number_skipped + 1
        result_text = f'''submission {i} : Images missing. Skipping'''
        return result_text, number_skipped
    # create successful submission log file if it doesnt exist
    try:
        file = open('successful_submissions.txt', 'r')
        file.close()
    except IOError:
        file = open('successful_submissions.txt', 'w')
        file.close()
        
    # skip if the submission was already made successfully
    with open('successful_submissions.txt', 'r') as f:
        if _uuid in f.read():
            result_text = f'''submission {i} : Already done. Skipping'''
            return result_text, number_skipped
            



        
            
    file_tuple = (_uuid, io.BytesIO(create_xml_submission(_uuid, csv_dict, xml_template)))
    files = {'xml_submission_file': file_tuple}

    for image in image_dict:
        file_name = image_dict[image]
        another_file_tuple = (file_name, open(file_name, 'rb'))
        files = {**files, file_name: another_file_tuple}
    res = ""
    headers = {'Authorization': f'Token {TOKEN}'}
    req = requests.Request(method='POST', url=SUBMISSION_URL, files=files, headers=headers ).prepare()
    
    
    num_retry = 0

    while num_retry < MAX_RETRIES:
        try:
            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            res = session.send(req)
            
            if res.status_code == 201:
                with open("successful_submissions.txt", "a") as successfile:
                    successfile.write(_uuid + "\n")
                result_text = f'''submission {i} : {res.status_code} : Success'''
                return result_text, number_skipped
            if res.status_code == 202:
                with open("successful_submissions.txt", "a") as successfile:
                    successfile.write(_uuid + "\n")
                result_text = f'''submission {i} : {res.status_code} : Duplicate submission. Continuing.'''
                return result_text, number_skipped
            print (f'''
submission {i} : {res.status_code} : Server returned error. Response:
    {res.text}
Retrying...
    ''')
            num_retry = num_retry + 1
        except requests.Timeout as error:
            num_retry = num_retry + 1
            print(f'''submission {i} : Timeout: {error}. Retrying...''')
        except requests.ConnectionError as error:
            num_retry = num_retry + 1
            print (f'''submission {i} : Connection error: {error}. Retrying...''')            
            sleep(5)
    number_skipped = number_skipped + 1
    result_text = f'''submission {i} : Skipping.''', number_skipped
    return result_text, number_skipped
    
    
def get_image_path(image_name, uuid, urls_dict):
    paths = []
    startpath = ".\\"
    for path in Path(f"{PHOTO_PATH}").glob(f"*/attachments/*/{uuid}/{image_name}"):
        path = startpath+str(path)
        paths.append(path)
        
  
    if len(paths) > 1:
        print(f'''WARNING: multiple paths found for {image_name}: 
        {paths}
        Using the first path found.''')
    if len(paths) == 0:
        print(f'''WARNING: image {image_name} not found at {PHOTO_PATH}/*/attachments/*/{uuid}/{image_name}. Check  that images are unzipped in the correct location. PHOTO_PATH can be changed in "upload_config.py". Verify the media is marked correctly in correspondance template. Trying to download...''')
        
        trimlength = len(BASE_URL) + 27
        alt_path = str(Path(f"{PHOTO_PATH}"+urls_dict[image_name].replace("%2F","/")[trimlength:]))
        slash = [m.start() for m in re.finditer(r"\\",alt_path)]
        alt_path = startpath + alt_path[:slash[3]+1]+ uuid + alt_path[slash[4]:]
        url = urls_dict[image_name]
        
        try:
            image_data = requests.get(url)
            os.makedirs(os.path.dirname(alt_path), exist_ok=True)
            with open(alt_path, 'wb') as f:
                f.write(image_data.content)
            print(f'''{image_name} saved to {alt_path}''')

            paths.append(alt_path)
        except:
            traceback.print_exc()
            print(f'''failed, adding to missing images file''')
            # write missing image and url to missing images file  
            try:
                file = open('missing_images.txt', 'r')
                file.close()
            except IOError:
                file = open('missing_images.txt', 'w')
                file.close()
            with open("missing_images.txt", "r") as f:
                if image not in f.read():
                    open("missing_images.txt", "a").write(image + ", " + url + ", " + image_path + "\n")
        
    
    return paths[0]



def get_xml_data ():
    import pandas as pd
    xml_df = pd.DataFrame(pd.read_excel(CORRESPONDANCE_FILE, sheet_name="result", header=0))
    xml_template_pd             = xml_df.loc[: , "generated_xml"]
    xml_template = '\n'.join([str(line) for line in xml_template_pd])
    #print(xml_template_pd)
    
    media_now                   = xml_df.loc[: , "media_now"]
    headings_to_use    = xml_df.loc[: , "oldQs_full"]
    media_dict = dict(zip(headings_to_use, media_now))
    xml_data = [xml_template , headings_to_use , media_dict, media_now]
    return xml_data



def get_submission_data(headings_to_use):
    import pandas as pd
    submissiondata_df = pd.DataFrame(pd.read_csv(DATA_FILE, encoding='utf-8', usecols = headings_to_use)).fillna('')
    print(submissiondata_df)
    return submissiondata_df



def prepare_submission(i, xml_data, submissiondata_df):
    xml_template = xml_data[0] 
    headings_to_use = xml_data[1] 
    media_dict = xml_data[2] 
    media_now = xml_data[3] 
    csv_dict = {}
    image_path = None
    image_names = []
    image_dict = {}
    urls_dict = {}
    
    this_row = submissiondata_df.iloc[i][headings_to_use]
    
    #read vars:
    for j in range(0, len(headings_to_use)):
        try:
            this_data = this_row[j].replace("<","&#60;").replace("&","&#38;").replace(">","&#62;").replace("'","&#39;").replace('"',"&#34;")
        except:
            this_data = this_row[j]
        csv_dict = {**csv_dict, headings_to_use[j]: this_data} 
        
        #collect image names
        if media_now[j]:
            #spaces in image names are replaced by kobo server with underscore, but remain as spaces in the database
            image_name = this_row[j].replace(" ","_")
            image_url = this_row[j+1]
            notnan = not(image_name == '' or (isinstance(image_name, float) and  math.isnan(image_name)))
            if notnan:
                image_names.append(image_name)
                urls_dict = {**urls_dict, image_name: image_url} 
    # add any images to the image dictionary
    missing_images = 0
    for image in image_names:
        try: 
            this_uuid = csv_dict["_uuid"]
            try:
                image_path = get_image_path(image, this_uuid, urls_dict)
                image_dict = {**image_dict, image : image_path}    
            except Exception:
                print("missing image error")
                traceback.print_exc()
                missing_images = missing_images + 1
        except Exception:
            print(f"uuid for {image} not found" )
            traceback.print_exc()
           
    return csv_dict, image_dict, missing_images



if __name__ == '__main__':
    print('''
    ''')
    xml_data = get_xml_data ()
    xml_template = xml_data[0]
    headings_to_use = xml_data[1]
    
    submissiondata_df = get_submission_data(headings_to_use)
    number_skipped = 0
    
    for i in range(0, len(submissiondata_df)):
        csv_dict, image_dict, missing_images = prepare_submission(i, xml_data, submissiondata_df)
        
        res, number_skipped = submit_data(i, csv_dict, headings_to_use, xml_template, image_dict, missing_images, number_skipped)
        print(res)
    print("Done. Number skipped: " + str(number_skipped))
