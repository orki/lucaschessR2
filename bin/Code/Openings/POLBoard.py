import collections

from PySide6 import QtWidgets, QtCore, QtGui

import Code.Nags.Nags
from Code.Base import Game, Move
from Code.Base.Constantes import GOOD_MOVE, VERY_GOOD_MOVE, NO_RATING, MISTAKE, BLUNDER, INTERESTING_MOVE, INACCURACY
from Code.Nags.Nags import NAG_1, NAG_2, NAG_3, NAG_4, NAG_5, NAG_6, dic_symbol_nags

from Code.Board import Board
from Code.QT import Colocacion
from Code.QT import Controles
from Code.QT import Iconos
from Code.QT import QTUtil
from Code.QT import QTVarios

V_SIN, V_IGUAL, V_BLANCAS, V_NEGRAS, V_BLANCAS_MAS, V_NEGRAS_MAS, V_BLANCAS_MAS_MAS, V_NEGRAS_MAS_MAS = (
    0,
    10,
    14,
    15,
    16,
    17,
    18,
    19,
)


class LBKey(Controles.LB):
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            if not self.game:
                return
            event.ignore()
            menu = QTVarios.LCMenu(self)
            menu.opcion("copy", _("Copy"), Iconos.Clipboard())
            menu.opcion("copy_sel", _("Copy to selected position"), Iconos.Clipboard())
            resp = menu.lanza()
            if resp == "copy":
                QTUtil.ponPortapapeles(self.game.pgn())
            elif resp == "copy_sel":
                g = self.game.copia(self.pos_move)
                QTUtil.ponPortapapeles(g.pgn())


class BoardLines(QtWidgets.QWidget):
    def __init__(self, panelOpening, configuration):
        QtWidgets.QWidget.__init__(self)

        self.panelOpening = panelOpening
        self.dbop = panelOpening.dbop

        self.configuration = configuration

        self.gamebase = panelOpening.gamebase
        self.num_jg_inicial = len(self.gamebase)
        self.pos_move = self.num_jg_inicial

        config_board = configuration.config_board("POSLINES", 32)
        self.board = Board.Board(self, config_board)
        self.board.crea()
        self.board.set_side_bottom(True)
        self.board.set_dispatcher(self.player_has_moved)
        self.board.dispatchSize(self.ajustaAncho)
        self.board.dbvisual_set_file(self.dbop.nom_fichero)
        self.board.dbvisual_set_show_always(True)
        self.board.dbvisual_set_save_always(True)

        self.board.set_side_bottom(self.dbop.getconfig("WHITEBOTTOM", True))

        self.dbop.setdbVisual_Board(self.board)  # To close

        tipo_letra = Controles.TipoLetra(puntos=configuration.x_pgn_fontpoints)

        lybt, bt = QTVarios.ly_mini_buttons(self, "", siTiempo=True, siLibre=False, icon_size=24)

        self.lbPGN = LBKey(
            self, " "
        ).set_wrap()  # Por alguna razón es necesario ese espacio en blanco, para aperturas sin movs iniciales
        self.lbPGN.setAlignment(QtCore.Qt.AlignTop)
        self.configuration.set_property(self.lbPGN, "pgn")
        self.lbPGN.ponFuente(tipo_letra)
        self.lbPGN.setOpenExternalLinks(False)

        def muestraPos(txt):
            self.colocatePartida(int(txt))

        self.lbPGN.linkActivated.connect(muestraPos)

        scroll = QtWidgets.QScrollArea()
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QtWidgets.QFrame.NoFrame)

        # ly = Colocacion.V().control(self.lbPGN).margen(0)
        # w_pgn = QtWidgets.QWidget()
        # w_pgn.setLayout(ly)
        scroll.setWidget(self.lbPGN)
        scroll.setMaximumHeight(configuration.x_pgn_fontpoints * 6)

        self.with_figurines = configuration.x_pgn_withfigurines

        dic_nags = Code.Nags.Nags.dic_nags()
        dicValoracion = collections.OrderedDict()
        dicValoracion[GOOD_MOVE] = (dic_nags[NAG_1].text, dic_symbol_nags(NAG_1))
        dicValoracion[MISTAKE] = (dic_nags[NAG_2].text, dic_symbol_nags(NAG_2))
        dicValoracion[VERY_GOOD_MOVE] = (dic_nags[NAG_3].text, dic_symbol_nags(NAG_3))
        dicValoracion[BLUNDER] = (dic_nags[NAG_4].text, dic_symbol_nags(NAG_4))
        dicValoracion[INTERESTING_MOVE] = (dic_nags[NAG_5].text, dic_symbol_nags(NAG_5))
        dicValoracion[INACCURACY] = (dic_nags[NAG_6].text, dic_symbol_nags(NAG_6))
        dicValoracion[NO_RATING] = (_("No rating"), "")

        self.dicVentaja = collections.OrderedDict()
        self.dicVentaja[V_SIN] = (_("Undefined"), QtGui.QIcon())
        self.dicVentaja[V_IGUAL] = (dic_nags[10].text, Iconos.V_Blancas_Igual_Negras())
        self.dicVentaja[V_BLANCAS] = (dic_nags[14].text, Iconos.V_Blancas())
        self.dicVentaja[V_BLANCAS_MAS] = (dic_nags[16].text, Iconos.V_Blancas_Mas())
        self.dicVentaja[V_BLANCAS_MAS_MAS] = (dic_nags[18].text, Iconos.V_Blancas_Mas_Mas())
        self.dicVentaja[V_NEGRAS] = (dic_nags[15].text, Iconos.V_Negras())
        self.dicVentaja[V_NEGRAS_MAS] = (dic_nags[17].text, Iconos.V_Negras_Mas())
        self.dicVentaja[V_NEGRAS_MAS_MAS] = (dic_nags[19].text, Iconos.V_Negras_Mas_Mas())

        # Valoracion
        li_options = [(tit[1] + " " + tit[0], k) for k, tit in dicValoracion.items()]
        self.cbValoracion = Controles.CB(self, li_options, 0).capture_changes(self.cambiadoValoracion)
        self.cbValoracion.ponFuente(tipo_letra)

        # Ventaja
        li_options = [(tit, k, icon) for k, (tit, icon) in self.dicVentaja.items()]
        self.cbVentaja = Controles.CB(self, li_options, 0).capture_changes(self.cambiadoVentaja)
        self.cbVentaja.ponFuente(tipo_letra)

        # Comentario
        self.emComentario = Controles.EM(self, siHTML=False).capturaCambios(self.cambiadoComentario)
        self.emComentario.ponFuente(tipo_letra)
        self.emComentario.altoMinimo(2 * configuration.x_pgn_rowheight)
        lyVal = Colocacion.H().control(self.cbValoracion).control(self.cbVentaja)
        lyEd = Colocacion.V().otro(lyVal).control(self.emComentario)

        # Opening
        self.lb_opening = Controles.LB(self).align_center().ponFuente(tipo_letra).set_wrap()

        lyt = Colocacion.H().relleno().control(self.board).relleno()

        lya = Colocacion.H().relleno().control(scroll).relleno()

        layout = Colocacion.V()
        layout.otro(lyt)
        layout.otro(lybt)
        layout.otro(lya)
        layout.otro(lyEd)
        layout.control(self.lb_opening)
        layout.margen(0)
        self.setLayout(layout)

        self.ajustaAncho()

        self.siReloj = False

        self.ponPartida(self.gamebase)

    def ponPartida(self, game):
        game.test_apertura()
        self.game = game
        label = game.rotuloOpening()
        self.lb_opening.set_text(label)

    def process_toolbar(self):
        getattr(self, self.sender().key)()

    def setvalue(self, key, valor):
        if self.fenm2:
            dic = self.dbop.getfenvalue(self.fenm2)
            dic[key] = valor
            self.dbop.setfenvalue(self.fenm2, dic)

            self.panelOpening.refresh_glines()

    def cambiadoValoracion(self):
        self.setvalue("VALORACION", self.cbValoracion.valor())

    def cambiadoVentaja(self):
        self.setvalue("VENTAJA", self.cbVentaja.valor())

    def cambiadoComentario(self):
        self.setvalue("COMENTARIO", self.emComentario.texto().strip())

    def ajustaAncho(self):
        self.setFixedWidth(self.board.ancho + 20)
        self.lbPGN.anchoFijo(self.board.ancho)

    def camposEdicion(self, siVisible):
        if self.siMoves:
            self.lbValoracion.setVisible(siVisible)
            self.cbValoracion.setVisible(siVisible)
            self.lbVentaja.setVisible(siVisible)
            self.cbVentaja.setVisible(siVisible)
            self.emComentario.setVisible(siVisible)

    def player_has_moved(self, from_sq, to_sq, promotion=""):
        cpActual = self.game.move(self.pos_move).position if self.pos_move >= 0 else self.game.first_position
        if cpActual.siPeonCoronando(from_sq, to_sq):
            promotion = self.board.peonCoronando(cpActual.is_white)

        ok, mens, move = Move.get_game_move(self.game, cpActual, from_sq, to_sq, promotion)

        if ok:
            game = Game.Game()
            game.assign_other_game(self.game)

            if self.pos_move < len(self.game) - 1:
                game.li_moves = game.li_moves[: self.pos_move + 1]
            game.add_move(move)
            self.panelOpening.player_has_moved(game)

    def resetValues(self):
        self.cbValoracion.set_value(NO_RATING)
        self.cbVentaja.set_value(V_SIN)
        self.emComentario.set_text("")

    def colocatePartida(self, pos):
        self.fenm2 = None
        num_jugadas = len(self.game)
        if num_jugadas == 0:
            self.pos_move = -1
            self.lbPGN.game = None
            self.lbPGN.set_text("")
            self.board.set_position(self.game.first_position)
            self.resetValues()
            self.activaPiezas()
            return

        if pos >= num_jugadas:
            self.siReloj = False
            pos = num_jugadas - 1
        elif pos < self.num_jg_inicial - 1:
            pos = self.num_jg_inicial - 1

        p = self.game

        numJugada = 1
        pgn = ""
        style_number = "color:%s; font-weight: bold;" % Code.dic_colors["PGN_NUMBER"]
        style_select = "color:%s;font-weight: bold;" % Code.dic_colors["PGN_SELECT"]
        style_moves = "color:%s;" % Code.dic_colors["PGN_MOVES"]
        salta = 0
        for n, move in enumerate(p.li_moves):
            if n % 2 == salta:
                pgn += '<span style="%s">%d.</span>' % (style_number, numJugada)
                numJugada += 1

            xp = move.pgn_html(self.with_figurines)
            if n == pos:
                xp = '<span style="%s">%s</span>' % (style_select, xp)
            else:
                xp = '<span style="%s">%s</span>' % (style_moves, xp)

            pgn += '<a href="%d" style="text-decoration:none;">%s</a> ' % (n, xp)

        self.lbPGN.set_text(pgn)
        self.lbPGN.game = self.game
        self.lbPGN.pos_move = pos

        self.pos_move = pos

        if pos < 0:
            self.board.set_position(self.game.first_position)
            self.resetValues()
            self.activaPiezas()
            return

        move = self.game.move(self.pos_move)
        position = move.position if move else self.game.first_position
        self.fenm2 = position.fenm2()
        dic = self.dbop.getfenvalue(self.fenm2)
        valoracion = dic.get("VALORACION", NO_RATING)
        ventaja = dic.get("VENTAJA", V_SIN)
        comment = dic.get("COMENTARIO", "")
        self.cbValoracion.set_value(valoracion)
        self.cbVentaja.set_value(ventaja)
        self.emComentario.set_text(comment)

        self.board.set_position(position)
        if move:
            self.board.put_arrow_sc(move.from_sq, move.to_sq)
            # position_before = move.position_before
            # fenM2_base = position_before.fenm2()

        if self.siReloj:
            self.board.disable_all()
        else:
            self.activaPiezas()

        self.panelOpening.setJugada(self.pos_move)

    def activaPiezas(self):
        self.board.disable_all()
        if not self.siReloj and self.pos_move >= self.num_jg_inicial - 1:
            if self.pos_move >= 0:
                move = self.game.move(self.pos_move)
                color = not move.is_white() if move else True
            else:
                color = True
            self.board.activate_side(color)

    def MoverInicio(self):
        self.colocatePartida(0)

    def MoverAtras(self):
        self.colocatePartida(self.pos_move - 1)

    def MoverAdelante(self):
        self.colocatePartida(self.pos_move + 1)

    def MoverFinal(self):
        self.colocatePartida(99999)

    def MoverTiempo(self):
        if self.siReloj:
            self.siReloj = False
        else:
            self.siReloj = True
            if self.pos_move == len(self.game) - 1:
                self.MoverInicio()
            self.lanzaReloj()
        self.activaPiezas()

    def toolbar_rightmouse(self):
        QTVarios.change_interval(self, self.configuration)

    def lanzaReloj(self):
        if self.siReloj:
            self.MoverAdelante()
            if self.configuration.x_beep_replay:
                Code.runSound.playBeep()
            QtCore.QTimer.singleShot(self.configuration.x_interval_replay, self.lanzaReloj)
