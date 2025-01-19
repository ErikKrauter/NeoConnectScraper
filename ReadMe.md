# **NeoConnectScraper**

NeoConnectScraper is a Python tool for web scraping and Google Sheets, and Google Drive automation.

---

## **Setup**


### **1. Clone repository**
Clone environment and cd into directory
```bash
https://github.com/ErikKrauter/NeoConnectScraper.git
```
```bash
cd NeoConnectScraper
```

### **2. Create a Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### **3. Install Dependecies**
```bash
pip install -r requirements.txt
```
## **Configuration**
### **1. .env File**
Create a .env file in the project root and add email and password for Neoss Login:

```bash
EMAIL=your_email@example.com
PASSWORD=your_password
EB=NameOfDoctorsForEB
LB=NameOfDoctorsForEB
OPENAI_API_KEY=YOUR_OPENAI_KEY
```
Note the names of the doctors have to match the names in the Neoss order.

### **2. credentials.json**
Place your google api credentials in the project root directory and name it credentials.json


## **Usage**
```bash
source .venv/bin/activate
python -m main
```