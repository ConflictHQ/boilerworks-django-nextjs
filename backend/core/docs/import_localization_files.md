# Localization file

## Requirements
* All files must be in json format
* The name of the file must be one of the languages codes supported (i.e. en, es)
* All files must be placed in the backend/domain_app/internationalization folder.

## How to import the file?
### Automatically on deploy
Via the 'load_localization_labels' command the files are automatically imported whenever the startup script is ran.
### Django Admin DataProcess
* Go to the data process ui https://{your-host}/app/admin/core/dataprocess/, and create a new process with the settings
  * File type: Json
  * Entity type: Site labels
  * Language: To your target language, file name is irrelevant in this context.
* Execute the process by selecting your data process record and applying the 'Process Data' action.

**Using this method does not modify the default files from the repository. In this case records might be replaced
on deployment, but won't be automatically removed.**

## Django Admin Site label
You can hotswap a label, by going to the https://{your-host}/app/admin/core/sitelabel/ page.
**Using this method does not modify the default files from the repository. In this case records might be replaced
on deployment, but won't be automatically removed.**

## Manually run python command
Running the following command will reload the localization files to the database,
```shell
python manage.py load_localization_labels
```
