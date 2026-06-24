FROM rclone/rclone:1.74.2@sha256:9ce0d49b611d3781233e25334e9e23d7af01e5546da7087f90d55f034ef13637 AS binaries

# final image
FROM alpine:3.24@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b

# copy the rclone binary from the official image
COPY --from=binaries /usr/local/bin/rclone /usr/local/bin/rclone

# copy startup and auth proxy scripts
COPY ["./docker/startup", "/startup"]
COPY ["./docker/auth-proxy.py", "/usr/local/bin/auth-proxy.py"]

# add python for the auth proxy script
RUN apk --no-cache add \
  python3 \
  ca-certificates \
  fuse3 \
  tzdata \
  && apk cache clean

# make scripts executable
RUN echo "user_allow_other" >> /etc/fuse.conf && \
  chmod +x /startup /usr/local/bin/auth-proxy.py

WORKDIR /data

ENV XDG_CONFIG_HOME=/config

# remote configs (used by auth-proxy.py)
ENV REMOTE_URL=""
ENV REMOTE_VENDOR=""

# s3 proxy configs
# a space separated list of options
ENV PROXY_ARGS=""

ENTRYPOINT [ "/startup" ]

EXPOSE 8080