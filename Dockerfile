FROM alpine:3.20
WORKDIR /ctx
COPY . .
RUN echo "=== BUILD CONTEXT CONTENTS (depth 4) ===" && \
    find . -maxdepth 4 -type f | sort && \
    echo "=== dataconnect-generated subtree ===" && \
    (ls -laR dataconnect-generated || echo "dataconnect-generated not present")
