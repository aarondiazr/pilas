# -*- encoding: utf-8 -*-
# Pilas engine - A video game framework.
#
# Copyright 2010 - Hugo Ruscitti
# License: LGPLv3 (see http://www.gnu.org/licenses/lgpl.html)
#
# Website - http://www.pilas-engine.com.ar

import pilas
from pilas.actores import Actor


class Mapa(Actor):
    """Representa mapas creados a partir de imagenes mas pequeñas.

    Este actor te permite crear escenarios tipo ``tiles``, una técnica
    de contrucción de escenarios muy popular en los videojuegos.
    
    Puedes crear un actor a partir de una grilla, e indicando cada
    uno los bloques o simplemente usando un programa externo llamado
    **tiled** (ver http://www.mapeditor.org).

    Por ejemplo, para crear un mapa desde un archivo del programa
    **tiled** puedes escribir:

        >>> mapa = pilas.actores.Mapa('untitled2.tmx')
    """

    def __init__(self, grilla_o_mapa=None, x=0, y=0, restitucion=0.56):
        Actor.__init__(self, 'invisible.png', x, y)
        self.restitucion = restitucion
        self.figuras = []
        self.bloques = []

        # Obtenemos el area de la ventana.
        self._ancho_mundo, self._alto_mundo = pilas.mundo.motor.obtener_area()

        if not grilla_o_mapa:
            grilla_o_mapa = grilla = pilas.imagenes.cargar_grilla("grillas/plataformas_10_10.png", 10, 10)
            
        self.grilla_o_mapa = grilla_o_mapa

        if isinstance(grilla_o_mapa, str):
            self._cargar_mapa(grilla_o_mapa)
        else:
            self.grilla = grilla_o_mapa
            self._ancho_cuadro = grilla_o_mapa.cuadro_ancho
            self._alto_cuadro = grilla_o_mapa.cuadro_alto
            self.superficie = None

        if (self.superficie != None):
            # Creamos un actor con la Superficie que hemos dibujado con los elementos de la capa 0 del mapa.
            superficie_mapa = pilas.actores.Actor(self.superficie)
            # Establecemos el nivel Z para que los Actores de las capas superiores se vean.
            superficie_mapa.z = 1
            # Establecemos la posición de la Superficie a partir de la esquina superior izquierda. 
            superficie_mapa.x += ((self.superficie.ancho()/2) - (self._ancho_mundo / 2))
            superficie_mapa.y -= ((self.superficie.alto()/2) - (self._alto_mundo / 2))

    def _cargar_mapa(self, archivo):
        "Carga el escenario desde un archivo .tmz (del programa tiled)."

        archivo = pilas.utils.obtener_ruta_al_recurso(archivo)

        # Carga los nodos principales.
        nodo = pilas.utils.xmlreader.makeRootNode(archivo)
        nodo_mapa = nodo.getChild('map')
        nodo_tileset = nodo_mapa.getChild('tileset')

        # Cantidad de bloques en el mapa.
        self.columnas = int(nodo_mapa.getAttributeValue('width'))
        self.filas = int(nodo_mapa.getAttributeValue('height'))

        # Atributos de la imagen asociada al mapa.
        self._ruta = nodo_tileset.getChild('image').getAttributeValue('source')
        self._ruta = pilas.utils.obtener_ruta_al_recurso(self._ruta)

        self._ancho_imagen = int(nodo_tileset.getChild('image').getAttributeValue('width'))
        self._alto_imagen = int(nodo_tileset.getChild('image').getAttributeValue('height'))
        self._ancho_cuadro = int(nodo_tileset.getAttributeValue('tilewidth'))
        self._alto_cuadro = int(nodo_tileset.getAttributeValue('tileheight'))

        # Creamos una Superficie para volcar el contenido del layer 0 del mapa.
        # El tamaño de la Superficie corresponde al tamaño del mapa.
        self.superficie = pilas.imagenes.cargar_superficie(self.columnas * self._ancho_cuadro, self.filas * self._alto_cuadro)

        # Carga la grilla de imagenes desde el mapa.
        self.grilla = pilas.imagenes.cargar_grilla(self._ruta, 
                self._ancho_imagen / self._ancho_cuadro, 
                self._alto_imagen / self._alto_cuadro)

        # Carga las capas del mapa.
        layers = nodo.getChild('map').getChildren('layer')

        if len(layers) == 0:
            raise Exception("Debe tener al menos una capa (layer).")

        # La capa 0 (inferior) define los bloques no-solidos.
        self._crear_bloques(layers[0], solidos=False)

        # El resto de las capas definen bloques solidos
        for layer in layers[1:]:
            self._crear_bloques(layer, solidos=True)

    def _crear_bloques(self, capa, solidos):
        "Genera actores que representan los bloques del escenario."
        datos = capa.getChild('data').getData()

        # Convierte todo el mapa en una matriz de numeros.
        bloques = [[int(x) for x in x.split(',') if x] for x in datos.split()]

        for (y, fila) in enumerate(bloques):
            for (x, bloque) in enumerate(fila):
                if bloque:
                    self.pintar_bloque(y, x, bloque -1, solidos)

    def pintar_bloque(self, fila, columna, indice, es_bloque_solido=True):
        
        if es_bloque_solido: # Solo definimos Actores para los elementos de las capas superiores.
            nuevo_bloque = pilas.actores.Actor('invisible.png')
            nuevo_bloque.imagen = self.grilla
            nuevo_bloque.imagen.definir_cuadro(indice)
            nuevo_bloque.izquierda = columna * self._ancho_cuadro - (self._ancho_mundo / 2)
            nuevo_bloque.arriba = -fila * self._alto_cuadro + (self._alto_mundo / 2)
            self.bloques.append(nuevo_bloque)
            figura = pilas.fisica.Rectangulo(nuevo_bloque.izquierda + self._ancho_cuadro / 2, 
                    nuevo_bloque.arriba - self._alto_cuadro / 2,
                    self._ancho_cuadro, self._alto_cuadro, dinamica=False, 
                    restitucion=self.restitucion)
            self.figuras.append(figura)
        else:
            # Definimos el cuadro que deseamos dibujar en la Superficie.
            self.grilla.definir_cuadro(indice)
            # Dibujamos el cuadro de la grilla en la Superficie.
            self.grilla.dibujarse_sobre_una_pizarra(self.superficie, columna * self._ancho_cuadro, fila * self._alto_cuadro)


    def reiniciar(self):
        self._eliminar_bloques()

        if isinstance(self.grilla_o_mapa, str):
            self._cargar_mapa(self.grilla_o_mapa)

    def eliminar(self):
        self._eliminar_bloques()

    def _eliminar_bloques(self):
        for b in self.bloques:
            b.eliminar()

        for f in self.figuras:
            f.eliminar()
