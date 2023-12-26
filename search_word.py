async def search_word_in_text(word, text):
    result = []
    word = word.lower()  # Ігноруємо регістр
    #words_in_text = text.split()
    text = text.split()
    text = text[0].lower()

    if text == word:
        return word

    #i = 0
    #similarity = 0
    #for char in word:
     #   if char == text[i]:
    #        similarity += 1
      #  i += 1

    #if similarity >= 3:
        #return result



