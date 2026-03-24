# Signed URL
1. [V4 signing process with Cloud Storage tools](https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#code-samples)
   1. Download/Upload Documents to Cloud Storage
1. CORS setup [Uploading user images to Google Cloud Storage](https://ryanbethel.org/uploading-user-images-to-google-cloud-storage)

1. [django-storages](https://django-storages.readthedocs.io/en/latest/backends/gcloud.html)
1. bucket [boilerworks-labs](https://console.cloud.google.com/storage/browser/boilerworks-labs;tab=permissions?forceOnBucketsSortingFiltering=false&authuser=1&project=boilerworks&prefix=&forceOnObjectsSortingFiltering=false)
1. To authenticate locally
   1. gcloud auth application-default login
   1. gcloud config set project boilerworks

# Upload files Directly
1. [Allowing Users to Upload Files](https://cloud.google.com/appengine/docs/standard/php/googlestorage/user_upload)
1. [Signed-URLs](https://cloud.google.com/storage/docs/access-control#Signed-URLs)

# Upload files with Django
1. [Storage Signed Url with custom headers ](https://github.com/googleapis/google-cloud-php/issues/1108)
