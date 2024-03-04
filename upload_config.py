# upload_config.py
# see readme for more info

#get token from kobo webpage under account settings -> security -> APIkey
TOKEN = 'paste_token_here'

#get form_UID from the form url eg https://kobo.humanitarianresponse.info/#/forms/[form_uid]/landing
FORM_UID = "paste_form_uid_here"

#change if needed, either https://kc.kobotoolbox.org or https://kc.humanitarianresponse.info
BASE_URL = 'https://kc.humanitarianresponse.info'
SUBMISSION_URL = f'{BASE_URL}/api/v1/submissions'

#names/ locations of required files
DATA_FILE = 'submission_data.csv'
CORRESPONDANCE_FILE = 'correspondance_template.xlsx'
PHOTO_PATH = "./photos/"


#maybe not working
SUBMIT_WITH_MISSING_IMAGES = False
MAX_RETRIES = 5
