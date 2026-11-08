FROM node:22

RUN npm install -g opencode-ai

WORKDIR /workspace

CMD ["bash"]