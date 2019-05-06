# our base image
FROM centos:latest

# Install python and pip
RUN yum install epel-release -y && yum install python-pip -y

# upgrade pip
RUN pip install --upgrade pip

# install Python modules needed by the Python app
RUN mkdir /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

# copy files required for the app to run
COPY app.py /usr/src/app/

# tell the port number the container should expose
EXPOSE 5000

# run the application
CMD ["python", "/usr/src/app/app.py"]
