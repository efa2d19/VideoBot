from aiohttp import ClientSession
import base64

from src.audio.tts.profane_filter import profane_filter


async def tts(
        client: 'ClientSession',
        req_text: str,
        filename: str,
        voice: str = 'en_us_002',  # List of valid voices in ValidVoices
):
    uri_base = 'https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/?text_speaker='
    req_text = profane_filter(req_text)
    output_text = ''

    # use multiple api requests to make the sentence
    if len(req_text) > 299:
        req_text_split = [req_text[i:i + 299] for i in range(0, len(req_text), 299)]
        for part in req_text_split:
            async with client.post(f'{uri_base}{voice}&req_text={part}&speaker_map_type=0') as result:
                response = await result.json()
                output_text += [response.get('data').get('v_str')][0]
        decoded_text = base64.b64decode(output_text)
        with open(filename, 'wb') as out:
            out.write(decoded_text)
        return

    # if under 299 characters do it in one
    async with client.post(f'{uri_base}{voice}&req_text={req_text}&speaker_map_type=0') as result:
        response = await result.json()
        output_text = [response.get('data').get('v_str')][0]
    decoded_text = base64.b64decode(output_text)
    with open(filename, 'wb') as out:
        out.write(decoded_text)
