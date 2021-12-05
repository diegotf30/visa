# Automatic US Visa appointment scheduling

This script uses Selenium to automatically schedule a US visa appointment

## Requerimientos

* Python 3.6+
* Firefox & [geckodriver](https://github.com/mozilla/geckodriver/releases). 
    * **Note:** Make sure that your geckodriver is in your [PATH](https://medium.com/@01luisrene/como-agregar-variables-de-entorno-s-o-windows-10-e7f38851f11f)

## Configuration
1. Install python library dependencies `pip install -r requirements.txt` (might be more than needed here, didn't use a venv)
2. Add credentials to `config.json`:
    * `sender_email` & `sender_email_password`: Used to send a notification email when an appointment is scheduled
    **Note:** if you have 2-factor auth you will need to generate an [app password](https://stackoverflow.com/a/60718806)
    * `notification_email`: Email that is being notified of scheduled appointment (generally the same as `sender_email`)
    * `visa_email` & `visa_email_password`: Credentails for the [us visa site](https://ais.usvisa-info.com/es-mx/niv/users/sign_in)


