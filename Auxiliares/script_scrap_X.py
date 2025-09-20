import time
from bs4 import BeautifulSoup as bs
import random
import time
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import random
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import Tk, ttk, messagebox, filedialog
import os


browser = uc.Chrome() #version_main=119
browser.get('https://x.com')


wait=input("en espera")


root = tk.Tk()
root.withdraw()
messagebox.showinfo("Save to", "Select a folder to save the results")
working_directory = filedialog.askdirectory()
root.destroy()

palabraclave='mercadona'

#2023-10-07"
# Fecha inicial  #### año-mes-día
fecha_actual = datetime.strptime("2025-05-31", "%Y-%m-%d")
fecha_limite = datetime.strptime("2015-05-31", "%Y-%m-%d")
count= 0

# Mientras la fecha actual sea mayor o igual que la fecha límite
while fecha_actual >= fecha_limite:
    
    exceldia = os.path.join(working_directory, f'{palabraclave} dia {fecha_actual.strftime("%Y-%m-%d")}.xlsx')
    
    df = pd.DataFrame()
    lista_usuarios=[]
    lista_fecha=[]
    lista_tweets=[]
    fecha_de_captura=[]
    
    
    
    # Imprime la fecha actual en el formato deseado (YYYY-MM-DD)
    #print(fecha_actual.strftime("%Y-%m-%d"))
    fecha_formateada_actual = fecha_actual.strftime("%Y-%m-%d") ### valores de bsuqueda
    fecha_actual_menos_1_día = fecha_actual
    fecha_actual_menos_1_día -= timedelta(days=1)
    fecha_menos_1_día_formateada = fecha_actual_menos_1_día.strftime("%Y-%m-%d") #### valores de busqueda
    

    url= f"https://x.com/search?q={palabraclave}%20lang%3Aes%20until%3A{fecha_formateada_actual}%20since%3A{fecha_menos_1_día_formateada}%20-filter%3Alinks%20-filter%3Areplies&src=typed_query"
    browser.get(url)
    print(url)
    time.sleep(5)
    print(10*'=')
    print('fecha actual ',fecha_actual)
    print('fecha actual format ', fecha_formateada_actual)
    print('fecha menos 1 día format ', fecha_menos_1_día_formateada)
    print(10*'=')
    
    count=0
    
    while count <= 35: #40
        count += 1 


        
        #buscar boton mostrtar más  
        # Encuentra todos los spans que contienen "Show more"
        time.sleep(7)

        try:
            show_more_buttons = browser.find_elements(By.XPATH, "//*[contains(text(), 'Show more')]")
            if show_more_buttons:
                for i, button in enumerate(show_more_buttons):
                    try:
                        # Clic directo por JavaScript, sin scroll
                        browser.execute_script("arguments[0].click();", button)
                        print(f"✅ Click  en botón {i+1}")
                        time.sleep(1)  # espera tras cada clic si se recarga contenido
                    except Exception as e:
                        print(f"❌ Error al hacer clic en botón {i+1}: {e}")
            else:
                print("ℹ️ No se encontró ningún botón 'Show more'")
        except Exception as e:
            print("ℹ️ No se encontró ningún botón 'Show more'.", e)
            
        html = browser.page_source
        soup = bs(html, 'lxml')
        # Encuentra todos los elementos div con el atributo 'data-testid' igual a "tweetText"
        tweets = soup.find_all('div', {'data-testid': 'tweetText'})
        tiempos=soup.find_all('time')
        users= soup.find_all('div',{'data-testid':"User-Name"})


        for user in users:
            usuario = user.text
            usuariosplit=usuario.split('@')
            print(10*'=')
            print(usuariosplit[0])
            lista_usuarios.append (usuariosplit[0])
            fecha_de_captura.append(fecha_formateada_actual) 


        for tiempo in tiempos:
            fecha = tiempo.text
            #print(10*'=')
            #print(fecha)
            lista_fecha.append(fecha)

        # Itera sobre los elementos encontrados
        for tuit in tweets:
            # texto de cada elemento
            texto_del_tuit = tuit.text #tuit.get_text(separator=" ", strip=True)
           # print(10*'=')
            #print(texto_del_tuit)
            lista_tweets.append(texto_del_tuit)
            
            

        scroll_distance = 1000  # ajuste distancia desplazamiento
        browser.execute_script(f"window.scrollBy(0, {scroll_distance});")

        #tiempo random para que evitar ban.
        tiempo_aleatorio = random.uniform(3, 10)
        time.sleep(tiempo_aleatorio)
        print(f'=========================== fin bucle numero {count} ==========================') 
        
        
    df['User']=lista_usuarios
    #df['fecha']=lista_fecha
    df['tweets']=lista_tweets
    df['search']= palabraclave ##################################################################################
    df['fecha_captura'] = fecha_de_captura
    # Utilizar duplicated() para encontrar filas duplicadas
    df.duplicated()
    df2=df.drop_duplicates() 
    df2.to_excel(exceldia, index=0)
    
    
    print('=========================== Descanso ==========================') 
    tiempo_aleatorio = random.uniform(40, 180) ####60,300
    time.sleep(tiempo_aleatorio)
    
    
    # Resta un día a la fecha actual
    fecha_actual -= timedelta(days=1)  ####final del bucle
    
    
print("===========================================================")    
print("===========================================================")  
print("===========================================================")  
print("===========================================================")  
print("===========================================================")  
print("===========================================================")  
print("===========================================================")  
print("===========================================================")  
print("===========================================================")  
print("EL PROCESO HA FINALIZADO")
print("===========================================================")  
