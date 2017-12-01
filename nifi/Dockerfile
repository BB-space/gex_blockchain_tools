FROM ubuntu:16.04
ENV TERM xterm
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

RUN apt-get update; apt-get install -y ssh sudo net-tools wget software-properties-common iputils-ping telnet dnsutils curl nano 

# Install Java 8
RUN add-apt-repository ppa:webupd8team/java
RUN apt-get update
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections
RUN apt-get install -q -y oracle-java8-installer oracle-java8-set-default

#NiFi
RUN wget apache.cp.if.ua/nifi/1.4.0/nifi-1.4.0-bin.tar.gz -O /usr/local/nifi-1.4.0-bin.tar.gz
RUN cd /usr/local; tar -xvzf nifi-1.4.0-bin.tar.gz && mv nifi-1.4.0 nifi && rm nifi-1.4.0-bin.tar.gz

ADD start.sh /usr/local/nifi/start.sh
CMD sh /usr/local/nifi/start.sh