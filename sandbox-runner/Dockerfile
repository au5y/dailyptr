# Minimal, disposable image used to compile & run one C++ submission.
# The web service launches a fresh `docker run --rm --network none ...`
# container from this image per submission, so it never needs anything
# beyond a compiler and coreutils.
FROM gcc:13-bookworm

RUN useradd -m -u 10001 sandboxuser
WORKDIR /sandbox
USER sandboxuser

# No CMD/ENTRYPOINT: the web service supplies the compile+run command
# for each submission via `docker run ... cpp-refresher-sandbox:latest <cmd>`.
