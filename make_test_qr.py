from pathlib import Path

import qrcode

TEST_LINKS = {
    'safe_rowan_admissions': 'https://www.rowan.edu/admissions',
    'safe_google_maps': 'https://www.google.com/maps',
    'safe_restaurant_menu': 'https://restaurant-menu.com/menu?table=4',
    'phish_paypal_lookalike': 'http://secure-paypa1-verify-account.xyz/login',
    'phish_wallet_free_host': 'https://metamask-wallet-restore.web.app',
    'phish_ip_bank_login': 'http://192.168.14.7/bank/login',
    'phish_amazon_subdomain': 'https://amazon.account-update-billing.top/signin',
}

out = Path(__file__).resolve().parent / 'test_qr_codes'
out.mkdir(exist_ok=True)
for name, link in TEST_LINKS.items():
    qrcode.make(link).save(out / f'{name}.png')
    print(f'{name}.png  ->  {link}')
