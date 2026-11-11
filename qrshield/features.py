import math
import re
from collections import Counter
from urllib.parse import urlsplit

import tldextract

_extract = tldextract.TLDExtract(suffix_list_urls=())

COMMON_TLDS = ['com', 'org', 'net', 'edu', 'gov', 'io', 'co', 'uk', 'de', 'fr', 'ru', 'in', 'br', 'au', 'jp',
               'info', 'xyz', 'top', 'app', 'dev', 'site', 'online', 'shop', 'live', 'click', 'link', 'me']

BRANDS = ['paypal', 'apple', 'icloud', 'microsoft', 'office', 'outlook', 'office365', 'onedrive', 'amazon',
          'netflix', 'google', 'gmail', 'facebook', 'instagram', 'whatsapp', 'meta', 'metamask', 'coinbase',
          'binance', 'chase', 'wellsfargo', 'bankofamerica', 'citi', 'usps', 'fedex', 'dhl', 'ups', 'irs',
          'adobe', 'docusign', 'dropbox', 'linkedin', 'steam', 'ebay', 'walmart', 'att', 'verizon', 'yahoo']

KEYWORDS = ['login', 'logon', 'signin', 'secure', 'verify', 'verification', 'account', 'update', 'support',
            'wallet', 'auth', 'bank', 'confirm', 'billing', 'payment', 'recover', 'unlock', 'webmail', 'service']

HOSTING = ['firebaseapp.com', 'web.app', 'ipfs.io', 'infura-ipfs.io', 'cloudflare-ipfs.com', 'dweb.link',
           'godaddysites.com', 'weebly.com', 'wixsite.com', 'blogspot.com', 'github.io', 'netlify.app',
           'vercel.app', 'pages.dev', 'workers.dev', 'herokuapp.com', '000webhostapp.com', 'glitch.me',
           'repl.co', 'square.site', 'webflow.io', 'r2.dev', 'appspot.com', 'azurewebsites.net',
           'web.core.windows.net', 'sharepoint.com', 'myshopify.com', 'gitbook.io', 'framer.app', 'weeblysite.com']

SERVICE_DOMAINS = ['google.com', 'googleapis.com', 'googleusercontent.com', 'goo.gl', 'forms.gle', 'sharepoint.com',
                   'live.com', 'office.com', 'onedrive.com', '1drv.ms', 'dropbox.com', 'box.com', 'notion.site',
                   'canva.site', 'jotform.com', 'typeform.com', 'amazonaws.com', 'cloudfront.net', 'windows.net']

SHORTENERS = ['bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'ow.ly', 'rebrand.ly', 'cutt.ly', 'shorturl.at', 'tiny.cc',
              'rb.gy', 'qrco.de', 'qr.codes', 'linktr.ee', 'buff.ly', 's.id']

IP_PATTERN = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
LOOKALIKE = str.maketrans({'0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'})


def parse_host(url):
    url = url.strip()
    if '://' not in url:
        url = 'http://' + url
    host = (urlsplit(url).hostname or '').lower().rstrip('.')
    if host.startswith('www.'):
        host = host[4:]
    return host


def registered_domain(host):
    parts = _extract(host)
    return f'{parts.domain}.{parts.suffix}' if parts.suffix else parts.domain


def platform_type(url):
    host = parse_host(url)
    registered = registered_domain(host)
    if registered in SHORTENERS or host in SHORTENERS:
        return 'shortener'
    if registered in SERVICE_DOMAINS or any(host.endswith('.' + d) for d in SERVICE_DOMAINS):
        return 'service'
    if any(host == h or host.endswith('.' + h) for h in HOSTING):
        return 'hosting'
    return None


def hosting_subdomain_signals(url):
    host = parse_host(url)
    platform = next((h for h in HOSTING if host == h or host.endswith('.' + h)), None)
    sub = host[: -len(platform)].rstrip('.') if platform and host != platform else ''
    signals = []
    if any(b in sub for b in BRANDS):
        signals.append('brand name on a free website platform')
    elif any(b in sub.translate(LOOKALIKE) for b in BRANDS if len(b) > 3):
        signals.append('imitates a brand name with look-alike characters')
    if any(k in sub for k in KEYWORDS):
        signals.append('contains words like login, verify or account')
    return signals


def entropy(text):
    if not text:
        return 0.0
    counts = Counter(text)
    return -sum(c / len(text) * math.log2(c / len(text)) for c in counts.values())


def host_features(url):
    host = parse_host(url)
    parts = _extract(host)
    domain = parts.domain
    suffix = parts.suffix
    registered = f'{domain}.{suffix}' if suffix else domain
    subdomain = parts.subdomain
    letters = sum(ch.isalpha() for ch in host)
    digits = sum(ch.isdigit() for ch in host)
    vowels = sum(ch in 'aeiou' for ch in domain)
    tld = suffix.split('.')[-1] if suffix else ''

    f = {
        'host_length': len(host),
        'domain_length': len(domain),
        'subdomain_length': len(subdomain),
        'subdomain_count': len(subdomain.split('.')) if subdomain else 0,
        'dot_count': host.count('.'),
        'hyphen_count': host.count('-'),
        'domain_hyphen_count': domain.count('-'),
        'digit_count': digits,
        'digit_ratio': digits / max(len(host), 1),
        'letter_ratio': letters / max(len(host), 1),
        'domain_vowel_ratio': vowels / max(len(domain), 1),
        'domain_entropy': entropy(domain),
        'subdomain_entropy': entropy(subdomain),
        'is_ip': int(bool(IP_PATTERN.match(host))),
        'has_punycode': int('xn--' in host),
        'suffix_parts': len(suffix.split('.')) if suffix else 0,
        'brand_in_host': int(any(b in host for b in BRANDS)),
        'brand_not_registered': int(any(b in host for b in BRANDS) and not any(b in domain for b in BRANDS)),
        'brand_lookalike': int(not any(b in host for b in BRANDS) and any(b in host.translate(LOOKALIKE) for b in BRANDS if len(b) > 3)),
        'keyword_count': sum(k in host for k in KEYWORDS),
    }
    for t in COMMON_TLDS:
        f[f'tld_{t}'] = int(tld == t)
    f['tld_other'] = int(tld not in COMMON_TLDS)
    return f


def naive_features(url):
    raw = url.strip()
    split = urlsplit(raw if '://' in raw else 'http://' + raw)
    f = host_features(raw)
    f.update({
        'url_length': len(raw),
        'path_length': len(split.path.strip('/')),
        'has_path': int(len(split.path.strip('/')) > 0),
        'has_query': int(bool(split.query)),
        'slash_count': raw.count('/'),
        'is_https': int(raw.lower().startswith('https://')),
        'has_www': int('://www.' in raw.lower() or raw.lower().startswith('www.')),
    })
    return f


FEATURE_NAMES = list(host_features('https://example.com').keys())
NAIVE_FEATURE_NAMES = list(naive_features('https://example.com').keys())

FRIENDLY = {
    'host_length': 'unusually long web address',
    'domain_length': 'unusual domain name length',
    'subdomain_length': 'long subdomain part',
    'subdomain_count': 'many subdomains stacked together',
    'dot_count': 'many dots in the address',
    'hyphen_count': 'many dashes in the address',
    'domain_hyphen_count': 'dashes in the main domain name',
    'digit_count': 'many numbers in the address',
    'digit_ratio': 'high share of numbers in the address',
    'letter_ratio': 'unusual mix of characters',
    'domain_vowel_ratio': 'domain name looks random',
    'domain_entropy': 'domain name looks random',
    'subdomain_entropy': 'subdomain looks random',
    'is_ip': 'uses an IP address instead of a name',
    'has_punycode': 'uses look-alike international characters',
    'suffix_parts': 'unusual domain ending',
    'brand_in_host': 'mentions a well-known brand',
    'brand_not_registered': 'brand name used on a domain the brand does not own',
    'brand_lookalike': 'imitates a brand name with look-alike characters',
    'keyword_count': 'contains words like login, verify or account',
    'tld_other': 'rare domain ending',
}


def friendly_name(feature, url):
    if feature.startswith('tld_') and feature != 'tld_other':
        return f'domain ending .{feature[4:]}'
    return FRIENDLY.get(feature, feature)
