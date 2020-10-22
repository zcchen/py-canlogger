DOCKERNAME = canlogger
DOCKER_VER = latest

BUILD_DIR  = build
LOG_DIR    = log

docker: $(BUILD_DIR)
	docker build $(CURDIR) -t $(DOCKERNAME):$(DOCKER_VER)

package: docker
	docker save $(DOCKERNAME):$(DOCKER_VER) | gzip > $(BUILD_DIR)/$(DOCKERNAME)_$(DOCKER_VER).docker.gz

clean:
	-rm -fvr $(BUILD_DIR)
	-docker rmi -f $(DOCKERNAME):$(DOCKER_VER)

run:
	docker run --rm -it --network host --cap-add=ALL --privileged \
		-v $(CURDIR)/$(LOG_DIR):/canlog \
		canlogger /canlog/canlog_`date +"%Y-%m-%d_%H-%M-%S"`.csv


$(BUILD_DIR):
	mkdir -p $@

