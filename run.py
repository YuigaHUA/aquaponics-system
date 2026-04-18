from app import create_app, socketio


app = create_app()

if __name__ == "__main__":
    socketio.run(
        app,
        host=app.config["APP_HOST"],
        port=app.config["APP_PORT"],
        debug=app.config["DEBUG"],
        allow_unsafe_werkzeug=True,
        use_reloader=False,
    )
