import PyPDF2
path=r"c:\Users\nikhi\OneDrive\Desktop\BE PROJECT (5)\BE PROJECT\UPVEST_REVISED_RESEARCH_PAPER (1).pdf"
reader=PyPDF2.PdfReader(path)
for i,p in enumerate(reader.pages[:3]):
    print('--- page', i+1)
    text=p.extract_text()
    if text:
        print(text[:1000])
    else:
        print('<no text>')
