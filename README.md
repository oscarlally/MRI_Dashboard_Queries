# MRI_Dashboard_Queries
Allows the user to make easy SQL queries to the GSTT MRI Physics Dashboard Database (stored on the minimac).

This also contains code that links with the dashboard to alert the user if scanners are not sending data over to the shared drive.  To download the code, please run the following.

Please ensure you have downloaded Github desktop on your computer (this is not a neccessity but it means that updates are automatically changed on your computer). This script can either be run locally or in a venv.  For either method, navigate to the folder on your computer where you want to save the code.  Once you have done this, open a terminal in that location and run the following command:

```python
git clone https://github.com/oscarlally/MRI_Dashboard_Queries
```

If you want to do this via a virtual environment (RECOMMENDED), navigate to the project directory and run the below commands. 

```python
python3 -m venv venv

source venv/bin/activate

pip3 install -r requirements.txt
```

To run this script, navigate to the directory that you have saved this code in (usually /Users/yourname/Github/MRI_Dashboard_Queries), and run the following command:

```python
python3 main.py
```

