import requests, os
import datetime, schedule, time
import shutil, datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

print ('--- Container started ----')
backup_time = str(os.environ['BACKUP_TIME'])
source_list = str(os.environ['SOURCES_LIST'])
shared_service_folder = str(os.environ['GDRIVE_DESTINATION'])
service_account_json = "/simple_backup_config/credentials.json"
print ('Parameters: [' +backup_time +'] ['+source_list+'] ['+shared_service_folder+']')
current_directory = os.path.dirname(__file__)
backup_directory = current_directory + '/created_backups'

def make_archive(source, destination):
        base = os.path.basename(destination)
        name = base.split('.')[0]
        format = base.split('.')[1]
        archive_from = os.path.dirname(source)
        archive_to = os.path.basename(source.strip(os.sep))
        shutil.make_archive(name, format, archive_from, archive_to)
        shutil.move('%s.%s'%(name,format), destination)

def process_backups ():

    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)
    
    sources = source_list.split(';')
    
    i = 0

    for folder in sources:
        folder = '/host'+folder 
        if (os.path.exists(folder)):
            archive_name = os.path.split(folder)[1]+ '.zip'
            print ('Processing ZIP: '+ archive_name)
            make_archive(folder,backup_directory+'/'+archive_name)
            print ('Zip created: '+archive_name)
            i=i+1
        else:
            print ('['+folder+'] doesnt exist')
    
    if i == 0: 
        return False
    else:
        return True

def authentificate_gdrive():
    scope = ["https://www.googleapis.com/auth/drive"]
    gauth = GoogleAuth()
    gauth.auth_method = 'service'
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_json, scope)
    return GoogleDrive(gauth)

def create_folder(drive, parentFolder, folderName):
        file_metadata = ''
        folders = drive.ListFile({'q': "title='" + parentFolder + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        for folder in folders:
            if folder['title'] == parentFolder:
                file_metadata = {
                'title': folderName,
                'parents': [{'id': folder['id']}],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive.CreateFile(file_metadata)
            folder.Upload()
            print ('Folder created')

def upload_file(drive, destanation_folder, file):
    folders = drive.ListFile(
    {'q': "title='" + destanation_folder + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'] == destanation_folder:
            file_name = os.path.basename(file)
            file2 = drive.CreateFile({'parents': [{'id': folder['id']}], 'title': file_name})
            file2.SetContentFile(file)
            file2.Upload()
            print (file_name+' uploaded ')

def upload_backups():
    drive = authentificate_gdrive()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    create_folder(drive, shared_service_folder, date)
    for backup in os.listdir(backup_directory):
        upload_file(drive, date, backup_directory + '/' + backup)
    shutil.rmtree(backup_directory)

def init ():
    print ('Main procedure is initiated')
    result = process_backups()
    if (result): upload_backups()

schedule.every().day.at(backup_time).do(init)

while True:
    schedule.run_pending()
    time.sleep(60)
