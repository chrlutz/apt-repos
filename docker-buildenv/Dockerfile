FROM debian:bullseye

RUN mkdir /build

VOLUME /build

COPY debian_control /debian-build/control

RUN apt-get update && apt-get install -y \
        build-essential \
        devscripts \
        git \
        make && \
    mk-build-deps --tool 'apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends -y' --install /debian-build/control && \
    rm -rf /var/lib/apt/lists/* && \
    chmod 777 /debian-build && \
    mkdir -p /debian-build/build

VOLUME /debian-build/build/

CMD [ "make", "-C", "/debian-build/build", "debian-build-in-buildenv" ]
