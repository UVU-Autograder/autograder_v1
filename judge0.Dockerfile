FROM judge0/judge0:1.13.1

# Install pytest inside the custom Python 3.8.1 environment used by the Judge0 sandbox
RUN /usr/local/python-3.8.1/bin/pip3 install pytest
