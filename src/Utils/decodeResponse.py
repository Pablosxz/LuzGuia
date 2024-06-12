import urllib

# Extrai informações da mensagem
def decode_text_to_dict(text):
    decoded_text = urllib.parse.unquote(text)    
    decoded_dict = {}    
    pairs = decoded_text.split('&')
    for pair in pairs:        
        key, value = pair.split('=')
        decoded_dict[key] = value     
    return decoded_dict