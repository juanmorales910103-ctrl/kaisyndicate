import subprocess
import logging

class SystemNotifier:
    @staticmethod
    def send_alert(title, message):
        logging.info(f"[{title}] {message}")
        try:
            clean_msg = str(message).replace('"', "'")
            clean_title = str(title).replace('"', "'")
            script = f'display notification "{clean_msg}" with title "{clean_title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        except Exception as e:
            logging.error(f"Error enviando notificación nativa: {e}")
