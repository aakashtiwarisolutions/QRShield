from .detector import Detector
from .features import parse_host, platform_type, hosting_subdomain_signals
from . import storage

PLATFORM_NOTES = {
    'shortener': 'link shortener hides the real destination',
    'service': 'shared service where anyone can publish content',
    'hosting': 'free website platform where anyone can publish',
}


class QRShield:
    def __init__(self, db_path=storage.DB_PATH, model_dir=None, save_history=True):
        self.detector = Detector() if model_dir is None else Detector(model_dir)
        self.db = storage.connect(db_path)
        self.save_history = save_history

    def check(self, url, source='api'):
        host = parse_host(url)
        listed = storage.lookup(self.db, host)
        platform = platform_type(url)
        if listed:
            result = {'url': url, 'host': host, 'risk': 1.0 if listed == 'PHISHING' else 0.0, 'verdict': listed,
                      'reasons': ['on your blocklist' if listed == 'PHISHING' else 'on your trusted list']}
        elif platform in ('shortener', 'service'):
            result = {'url': url, 'host': host, 'risk': None, 'verdict': 'CAUTION', 'reasons': [PLATFORM_NOTES[platform]]}
        elif platform == 'hosting':
            signals = hosting_subdomain_signals(url)
            result = {'url': url, 'host': host, 'risk': None, 'verdict': 'PHISHING' if signals else 'CAUTION',
                      'reasons': signals or [PLATFORM_NOTES['hosting']]}
        else:
            result = self.detector.check(url)
        result['scan_id'] = storage.log_scan(self.db, result, source) if self.save_history else None
        return result

    def mark_wrong(self, result):
        correct = 'PHISHING' if result['verdict'] in ('SAFE', 'CAUTION') else 'SAFE'
        if result.get('scan_id') is not None:
            storage.add_feedback(self.db, result['scan_id'], correct)
        storage.add_host(self.db, 'allowlist' if correct == 'SAFE' else 'blocklist', result['host'])
        return correct
