from flask import Blueprint

moralis_verify = Blueprint("moralis_verify", __name__)

@moralis_verify.route("/moralis-verify", methods=["GET", "POST", "HEAD", "OPTIONS"])
def moralis_verify_endpoint():
    return "", 200
