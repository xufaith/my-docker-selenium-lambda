FROM public.ecr.aws/lambda/python:3.11

# Install required system packages
RUN yum install -y \
    atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm unzip curl

# Download and extract Headless Chrome & Chromedriver
# ENV CHROME_VERSION=

RUN curl -L -o /tmp/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/linux64/chrome-linux64.zip && \
    curl -L -o /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chrome.zip -d /opt && \
    unzip /tmp/chromedriver.zip -d /opt && \
    mv /opt/chrome-linux64 /opt/chrome && \
    mv /opt/chromedriver-linux64 /opt/chromedriver && \
    chmod +x /opt/chrome/chrome /opt/chromedriver/chromedriver

# Install Python packages
RUN pip install selenium==4.31.0
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your app code
COPY main.py ./

# Set the Lambda entry point
CMD ["main.handler"]



# FROM public.ecr.aws/lambda/python@sha256:6163db246a3595eaa5f2acf88525aefa3837fa54c6c105a3b10d18e7183b2d2b as build
# RUN dnf install -y unzip && \
#     curl -Lo "/tmp/chromedriver-linux64.zip" "https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.84/linux64/chromedriver-linux64.zip" && \
#     curl -Lo "/tmp/chrome-linux64.zip" "https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.84/linux64/chrome-linux64.zip" && \
#     unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
#     unzip /tmp/chrome-linux64.zip -d /opt/

# RUN google-chrome --headless --no-sandbox --disable-gpu --remote-debugging-port=9222 https://google.com &


# FROM public.ecr.aws/lambda/python@sha256:6163db246a3595eaa5f2acf88525aefa3837fa54c6c105a3b10d18e7183b2d2b
# RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
#     libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
#     libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
#     xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm
# RUN pip install selenium==4.31.0
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY --from=build /opt/chrome-linux64 /opt/chrome
# COPY --from=build /opt/chromedriver-linux64 /opt/
# COPY main.py ./
# CMD [ "main.handler" ]
