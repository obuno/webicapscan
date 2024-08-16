FROM alpine:latest

MAINTAINER Obuno "obuno@protonmail.com"

ENV cicapBaseVersion="0.6.3" cicapModuleVersion="0.5.7"

WORKDIR /

# 1. create needed directories
RUN mkdir -p /tmp/install && mkdir -p /opt/c-icap && mkdir -p /var/log/c-icap/ && mkdir -p /run/clamav && \
	cd /tmp/install

# 2. install needed packages
RUN apk --update --no-cache add \
	autoconf \
	automake \
	bash \
	bzip2 \
	bzip2-dev \ 
	zlib \
	zlib-dev \
	curl \
	tar \
	gcc \
	make \
	g++ \
	git \
	libatomic \
	libtool \
	clamav \ 
	clamav-libunrar \
	iproute2 \
	htop \
	python3 \
	py3-pip

# 3. download c_icap, c_icap modules and install them 
RUN curl --silent --location --remote-name "http://downloads.sourceforge.net/project/c-icap/c-icap/0.6.x/c_icap-${cicapBaseVersion}.tar.gz" && \
	curl --silent --location --remote-name "https://sourceforge.net/projects/c-icap/files/c-icap-modules/0.5.x/c_icap_modules-${cicapModuleVersion}.tar.gz" && \
	tar -xzf "c_icap-${cicapBaseVersion}.tar.gz" && tar -xzf "c_icap_modules-${cicapModuleVersion}.tar.gz" && cd c_icap-${cicapBaseVersion} && \
	
	sed -i 's/HTTP\/1.0/HTTP\/1.1/g' utils/c-icap-client.c && \
	sed -i 's/HTTP\/1.0/HTTP\/1.1/g' info.c && \

	/bin/sh RECONF && \
	./configure --quiet --prefix=/opt/c-icap --enable-large-files && \
	make && make install && \
	
	cd ../c_icap_modules-${cicapModuleVersion}/ && ./configure --quiet --with-c-icap=/opt/c-icap --prefix=/opt/c-icap && \
	make && make install

# 4. compile SquidClamAV
RUN git clone https://github.com/darold/squidclamav.git && \
	cd squidclamav/ && \
	./configure --with-c-icap=/opt/c-icap && \
	# Reaplace HTTP 1.0 with HTTP 1.1
	sed -i 's/HTTP\/1.0/HTTP\/1.1/g' src/squidclamav.c && \
	make && make install

# 5. configure clamav
RUN chown clamav:clamav /run/clamav

# 6. clean up
RUN cd / && rm -rf /tmp/install && \
	apk del \
		autoconf \
		automake \
		bzip2 \
		bzip2-dev \ 
		zlib \
		zlib-dev \
		curl \
		tar \
		gcc \
		make \
		g++ && \
		rm -rf /opt/c-icap/etc/*.default

ADD ./opt /opt
ADD ./etc /etc

RUN chmod a+x /etc/periodic/hourly/*
RUN chmod a+x /etc/periodic/daily/*

COPY startup.sh /app/startup.sh
RUN chmod a+x /app/*.sh

COPY ./app/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip --break-system-packages
RUN pip install -r requirements.txt --break-system-packages

COPY ./app /app

CMD ["/bin/sh","-c","/app/startup.sh"]
