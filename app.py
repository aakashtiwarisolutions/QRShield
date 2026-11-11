import os

import streamlit as st

from qrshield.qr import decode_image_bytes, looks_like_url
from qrshield.service import QRShield
from qrshield import storage

SAVE_HISTORY = os.environ.get('QRSHIELD_SAVE_HISTORY', 'true').lower() == 'true'

st.set_page_config(page_title='QRShield', page_icon='🛡️', layout='centered')


@st.cache_resource
def get_shield():
    return QRShield(save_history=SAVE_HISTORY)


shield = get_shield()

st.title('QRShield')
st.write('Check a QR code before you open its link. The link is analysed, never visited.')

camera_tab, upload_tab, paste_tab = st.tabs(['Scan with camera', 'Upload QR image', 'Paste a link'])
url = None

with camera_tab:
    photo = st.camera_input('Point your camera at a QR code and take a photo')
    if photo:
        url = decode_image_bytes(photo.getvalue())
        if not url:
            st.warning('No QR code found. Move closer and make sure the code is sharp and well lit.')

with upload_tab:
    upload = st.file_uploader('Upload a photo or screenshot of a QR code', type=['png', 'jpg', 'jpeg'])
    if upload:
        url = decode_image_bytes(upload.getvalue())
        if not url:
            st.warning('No QR code found in this image.')

with paste_tab:
    typed = st.text_input('Paste a link to check')
    if typed:
        url = typed

if url:
    if not looks_like_url(url):
        st.info(f'This QR code does not contain a web link. It contains: {url}')
    else:
        result = shield.check(url, source='web')
        st.code(url, language=None)
        risk = '' if result['risk'] is None else f" Risk {result['risk'] * 100:.0f}%."
        if result['verdict'] == 'PHISHING':
            st.error(f'Likely phishing.{risk} Do not open this link.')
        elif result['verdict'] == 'CAUTION':
            st.warning('Be careful. QRShield cannot judge pages on this kind of site. '
                       'Only open it if you trust whoever gave you the QR code.')
        else:
            st.success(f'Looks safe.{risk}')
        if result['reasons']:
            st.write('**Main reasons:**')
            for reason in result['reasons']:
                st.write(f'- {reason}')
        if st.button('This result is wrong'):
            corrected = shield.mark_wrong(result)
            st.write(f"Thanks. {result['host']} is now saved as {corrected}.")

if SAVE_HISTORY:
    with st.expander('Recent scans (stored only on this device)'):
        rows = storage.recent_scans(shield.db, 15)
        if rows:
            st.table([dict(zip(['time', 'host', 'verdict', 'risk', 'source'], r)) for r in rows])
        else:
            st.write('No scans yet.')

st.caption('QRShield is a student research project. It can make mistakes, so stay careful with links that ask for passwords or payments.')
