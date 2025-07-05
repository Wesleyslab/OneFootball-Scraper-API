from scraping import coletar_titulos_noticias, coletar_detalhes_noticia

# Link da página de um time no OneFootball (ex: Flamengo)
link_time = "https://onefootball.com/pt-br/time/corinthians-1649"
link_noticia = "https://onefootball.com/pt-br/noticias/corinthians-provoca-palmeiras-apos-nova-derrota-para-o-chelsea-mundial-e-para-poucos-41332722"




titulos = coletar_titulos_noticias(link_time)
print(titulos)
#conteudo = coletar_detalhes_noticia(link_noticia)
#print (conteudo)