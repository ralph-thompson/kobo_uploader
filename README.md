# kobo_uploadscript to batch upload kobo data (and images) to another form or server
see below notes for usage

1/ prepare config file
----------------------
modify upload_config.py to match your API token, form uid, and base url.


2/ prepare submission_data.csv
------------------------------
to prepare the data you want to upload, download the excel data from kobo server by cliking on project -> data -> downloads.
export the data with these settings: 
*   select export type: xls
*   value and header format: xml values and headers
*   Export Select Many questions as… : Single column
*   Include data from all 9 versions : tick
*   Include groups in headers: tick
*   group separator: /
*   Store date and number responses as text : untick
*   Include media URLs : tick
download the exported file and place it in the same folder as the script.
in excel, open the downloaded file and click save as  with filename "submission_data" and file type CSV-UTF8

3/ define how to link the old data to the target form
-----------------------------------------------------
set up the correspondance_template to define how to link headings in the old data with headings in the target form. 
export data from the target form with "value and header format": "xml values and headers", and copy the first row into correspondance_template, into the column "new_headings" on the "input" tab
If the data you are uploading comes from a different version of the form than the target, copy the headings from the submission_data file and paste them into correspondance_template, into the column "old_headings" on the "input" tab. cut and paste the values until they line up correctly with the new headings.
If the data you are uploading has the same format, copy the xml headings into both the new and old headings columns
go through each line and put an x in the "mark_x_for_media" next to each new heading that will be a media file (tested with photos. milage may vary with other media types).
CORRESPONDANCE_FILE = 'correspondance_template.xlsx'

4/ add any media files
----------------------
to get all media, download from project -> data -> downloads and export type: media files/zip. 
create a folder next to the script called "photos" and unzip the downloaded zip archive into it.
for very large projects with many images, kobo server may timeout preparing or downloading the zip file. as a workaround:
	- open submission_data in excel and save as type webpage / html. 
	- you can open the created page in firefox and use downthemall or equivilent to download all the image files from their urls (make sure Include media URLs was ticked during data export if you cant see any urls). 
	- the images must be placed in the same file structure as the zipped kobo media export, otherwise the script wont find them. if you play around with the downthemall settings you can download them correctly

5/ run script
-------------
in powershell move to the folder with the script and run with :
python kobo_batchuploader.
if you get errors you may need to install the dependancies with pip or similar first.
successful uploads are recorded in successful_submissions.csv. if you rerun the script those lines will be skipped. so you can stop half way and rerun the script without issues.
