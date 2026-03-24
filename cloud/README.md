# Cloud Node Setup & Execution Guide

This document combines the system preparation for the cloud dashboard.

You can access through the next link: [Cloud Dashboard](https://your-iot-dashboard.streamlit.app)

---

## 1. Create a GitHub Repository

Streamlit Cloud pulls your code directly from GitHub.

1. Go to GitHub.com and create a free account (if you don't have one).
2. Create a new repository (you can name it something like Security_IoT).
3. Upload your dashboard.py file to this new repository.

## 2. Create a requirements.txt File
When your app runs on your computer, it uses the libraries you installed via pip. When it runs in the cloud, the cloud server needs to know what to install.

1. In your GitHub repository, create a new file and name it requirements.txt.
2. Paste the following text exactly as it is into that file:

```plaintext
streamlit
paho-mqtt
pandas
streamlit-autorefresh
```
3. Save (commit) the file.

## 3. Deploy to Streamlit Cloud
1. Go to share.streamlit.io and log in using your GitHub account.
2. Click the "New app" button.
3. Select your iot-security-dashboard repository.
4. Set the "Main file path" to dashboard.py.
5. Click "Deploy".