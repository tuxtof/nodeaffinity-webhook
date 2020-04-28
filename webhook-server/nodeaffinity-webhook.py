from flask import Flask, request, jsonify
import base64
import jsonpatch
import multiprocessing
import gunicorn.app.base

admission_controller = Flask(__name__)


@admission_controller.route('/health', methods=['GET'])
def pod_health():
    return "OK"


@admission_controller.route('/validate/pods', methods=['POST'])
def pod_webhook():
    request_info = request.get_json()
    # admission_controller.logger.warning("validate %s", request_info)
    # .get("nodeAffinity"):
    if request_info["request"]["object"]["spec"].get("affinity") and request_info["request"]["object"]["spec"]["affinity"].get("nodeAffinity"):
        return admission_response(True, "Allow because nodeAffinity exists")
    return admission_response(False, "Not allowed without nodeAffinity")


def admission_response(allowed, message):
    return jsonify({"response": {"allowed": allowed, "status": {"message": message}}})


@admission_controller.route('/mutate/isolated-pods', methods=['POST'])
def pod_webhook_mutate():
    request_info = request.get_json()
    # admission_controller.logger.warning("mutate %s", request_info)
    return admission_response_patch(True, "Adding nodeSelector ", json_patch=jsonpatch.JsonPatch([
        {
            "op": "replace",
            "path": "/spec/affinity",
            "value": {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {
                                        "key": "ns-affinity",
                                        "operator": "In",
                                        "values": [
                                            request_info["request"]["namespace"]
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    ]))


@admission_controller.route('/mutate/enforced-pods', methods=['POST'])
def pod_webhook_default_mutate():
    # admission_controller.logger.warning("mutate %s", request_info)
    return admission_response_patch(True, "Adding nodeSelector ", json_patch=jsonpatch.JsonPatch([
        {
            "op": "replace",
            "path": "/spec/affinity",
            "value": {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {
                                        "key": "ns-affinity",
                                        "operator": "DoesNotExist"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    ]))


def admission_response_patch(allowed, message, json_patch):
    base64_patch = base64.b64encode(
        json_patch.to_string().encode("utf-8")).decode("utf-8")
    return jsonify({"response": {"allowed": allowed,
                                 "status": {"message": message},
                                 "patchType": "JSONPatch",
                                 "patch": base64_patch}})


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


if __name__ == '__main__':
    options = {
        'bind': '0.0.0.0:443',
        'keyfile': '/webhook-ssl/key.pem',
        'certfile': '/webhook-ssl/cert.pem',
        'workers': number_of_workers(),
    }

    StandaloneApplication(admission_controller, options).run()
