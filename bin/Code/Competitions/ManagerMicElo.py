import datetime
import random

import Code
from Code import Adjournments
from Code import Manager
from Code import Util
from Code.Base import Move
from Code.Base.Constantes import (
    ST_ENDGAME,
    ST_PLAYING,
    RS_WIN_PLAYER,
    RS_WIN_OPPONENT,
    RS_DRAW,
    GT_MICELO,
    TB_TAKEBACK,
    TB_CONFIG,
    TB_ADJOURN,
    TB_CANCEL,
    TB_DRAW,
    TB_RESIGN,
    TB_UTILITIES,
    TERMINATION_RESIGN,
    WHITE,
    BLACK,
)
from Code.Engines import Engines
from Code.Engines import EnginesMicElo, EngineResponse
from Code.Polyglots import Books
from Code.QT import QTUtil2, QTUtil
from Code.SQL import UtilSQL


class DicMicElos:
    def __init__(self):
        self.variable = "DicMicElos"
        self.configuration = Code.configuration
        self._dic = self.configuration.read_variables(self.variable)

    def dic(self):
        return self._dic

    def cambia_elo(self, clave_motor, nuevo_elo):
        self._dic = self.configuration.read_variables(self.variable)
        self._dic[clave_motor] = nuevo_elo
        self.configuration.write_variables(self.variable, self._dic)


def lista():
    li = EnginesMicElo.all_engines()
    dic_elos = DicMicElos().dic()
    for mt in li:
        k = mt.alias
        if k in dic_elos:
            mt.elo = dic_elos[k]

    return li


class ManagerMicElo(Manager.Manager):
    li_t = None

    @staticmethod
    def calc_dif_elo(elo_jugador, elo_rival, resultado):
        if resultado == RS_WIN_PLAYER:
            result = 1
        elif resultado == RS_DRAW:
            result = 0
        else:
            result = -1
        return Util.fideELO(elo_jugador, elo_rival, result)

    def list_engines(self, elo):
        self.li_t = (
            (0, 50, 3),
            (20, 53, 5),
            (40, 58, 4),
            (60, 62, 4),
            (80, 66, 5),
            (100, 69, 4),
            (120, 73, 3),
            (140, 76, 3),
            (160, 79, 3),
            (180, 82, 2),
            (200, 84, 9),
            (300, 93, 4),
            (400, 97, 3),
        )
        # self.liK = ((0, 60), (800, 50), (1200, 40), (1600, 30), (2000, 30), (2400, 10))

        li = []
        self.liMotores = lista()
        numX = len(self.liMotores)
        for num, mt in enumerate(self.liMotores):
            mtElo = mt.elo
            mt.siJugable = abs(mtElo - elo) < 400
            mt.siOut = not mt.siJugable
            mt.baseElo = elo  # servira para rehacer la lista y elegir en aplazamiento
            if mt.siJugable or (mtElo > elo):

                def rot(res):
                    return self.calc_dif_elo(elo, mtElo, res)

                def rrot(res):
                    return self.calc_dif_elo(mtElo, elo, res)

                mt.pgana = rot(RS_WIN_PLAYER)
                mt.ptablas = rot(RS_DRAW)
                mt.ppierde = rot(RS_WIN_OPPONENT)

                mt.rgana = rrot(RS_WIN_PLAYER)
                mt.rtablas = rrot(RS_DRAW)
                mt.rpierde = rrot(RS_WIN_OPPONENT)

                mt.number = numX - num

                li.append(mt)

        return li

    def start(self, engine_rival, minutos, seconds):
        self.base_inicio(engine_rival, minutos, seconds)
        self.start_message()
        self.play_next_move()

    def base_inicio(self, engine_rival, minutos, seconds, human_side=None):
        self.game_type = GT_MICELO

        self.engine_rival = engine_rival
        self.minutos = minutos
        self.seconds = seconds

        self.is_competitive = True

        self.resultado = None
        self.human_is_playing = False
        self.state = ST_PLAYING
        self.showed_result = False  # Problema doble asignacion de ptos Thomas

        if human_side is None:
            is_white = self.determinaColor(engine_rival)
        else:
            is_white = human_side

        self.human_side = is_white
        self.is_engine_side_white = not is_white

        self.lirm_engine = []
        self.next_test_resign = 0
        self.resign_limit = -1000

        self.is_tutor_enabled = False
        self.main_window.set_activate_tutor(False)
        self.ayudas_iniciales = self.hints = 0

        self.vtime = {}
        self.max_seconds = minutos * 60
        self.secs_move = seconds

        self.vtime[True] = Util.Timer(self.max_seconds)
        self.vtime[False] = Util.Timer(self.max_seconds)
        self.vtime = {WHITE: Util.Timer(self.max_seconds), BLACK: Util.Timer(self.max_seconds)}

        cbook = self.engine_rival.book if self.engine_rival.book else Code.tbook
        self.book = Books.Book("P", cbook, cbook, True)
        self.book.polyglot()

        elo = self.engine_rival.elo
        self.maxMoveBook = (elo // 200) if 0 <= elo <= 1700 else 9999

        eloengine = self.engine_rival.elo
        eloplayer = self.configuration.miceloActivo()
        self.whiteElo = eloplayer if is_white else eloengine
        self.blackElo = eloplayer if not is_white else eloengine

        self.xrival = self.procesador.creaManagerMotor(
            self.engine_rival, None, None, siMultiPV=self.engine_rival.multiPV > 0
        )
        self.xrival.check_engine()

        self.pte_tool_resigndraw = False
        if self.human_side:
            self.pte_tool_resigndraw = True
            self.maxPlyRendirse = 1
        else:
            self.maxPlyRendirse = 0

        self.pon_toolbar()

        self.main_window.activaJuego(True, True, siAyudas=False)
        self.set_dispatcher(self.player_has_moved)
        self.set_position(self.game.last_position)
        self.put_pieces_bottom(is_white)
        self.remove_hints(True, siQuitarAtras=True)
        self.show_side_indicator(True)

        nbsp = "&nbsp;" * 3

        txt = "%s:%+d%s%s:%+d%s%s:%+d" % (
            _("Win"),
            self.engine_rival.pgana,
            nbsp,
            _("Draw"),
            self.engine_rival.ptablas,
            nbsp,
            _("Loss"),
            self.engine_rival.ppierde,
        )
        self.set_label1("<center>%s</center>" % txt)
        self.set_label2("")
        self.pgnRefresh(True)
        self.ponCapInfoPorDefecto()

        tpBL = self.vtime[True].etiqueta()
        tpNG = self.vtime[False].etiqueta()
        self.rival = self.engine_rival.alias + " (%d)" % self.engine_rival.elo
        white_name, black_name = self.configuration.nom_player(), self.engine_rival.alias
        white_elo, black_elo = self.configuration.miceloActivo(), self.engine_rival.elo
        if self.is_engine_side_white:
            white_name, black_name = black_name, white_name
            white_elo, black_elo = black_elo, white_elo

        self.game.set_tag("Event", _("Tourney-Elo"))

        self.game.set_tag("White", white_name)
        self.game.set_tag("Black", black_name)
        self.game.set_tag("WhiteElo", str(white_elo))
        self.game.set_tag("BlackElo", str(black_elo))

        time_control = "%d" % int(self.max_seconds)
        if self.secs_move:
            time_control += "+%d" % self.secs_move
        self.game.set_tag("TimeControl", time_control)

        white_player = white_name + " (%d)" % white_elo
        black_player = black_name + " (%d)" % black_elo

        self.main_window.ponDatosReloj(white_player, tpBL, black_player, tpNG)
        self.refresh()

        self.check_boards_setposition()

        self.game.tag_timestart()

    def pon_toolbar(self):
        if self.pte_tool_resigndraw:
            liTool = (TB_CANCEL, TB_ADJOURN, TB_TAKEBACK, TB_CONFIG, TB_UTILITIES)
        else:
            liTool = (TB_RESIGN, TB_DRAW, TB_ADJOURN, TB_CONFIG, TB_UTILITIES)

        self.set_toolbar(liTool)

    def run_action(self, key):

        if key in (TB_RESIGN, TB_CANCEL):
            self.rendirse()

        elif key == TB_DRAW:
            self.tablasPlayer()

        elif key == TB_CONFIG:
            self.configurar(siSonidos=True)

        elif key == TB_UTILITIES:
            self.utilidadesElo()

        elif key == TB_ADJOURN:
            self.adjourn()

        elif key in self.procesador.li_opciones_inicio:
            self.procesador.run_action(key)

        else:
            Manager.Manager.rutinaAccionDef(self, key)

    def save_state(self):
        self.main_window.stop_clock()

        self.vtime[self.human_side].stop_marker(0)

        dic = {
            "engine_rival": self.engine_rival.save(),
            "minutos": self.minutos,
            "seconds": self.seconds,
            "game_save": self.game.save(),
            "time_white": self.vtime[WHITE].save(),
            "time_black": self.vtime[BLACK].save(),
            "pgana": self.engine_rival.pgana,
            "ptablas": self.engine_rival.ptablas,
            "ppierde": self.engine_rival.ppierde,
            "alias": self.engine_rival.alias,
            "human_side": self.human_side,
        }

        return dic

    def restore_state(self, dic):
        engine_rival = Engines.Engine()
        engine_rival.restore(dic["engine_rival"])
        engine_rival.pgana = dic["pgana"]
        engine_rival.ptablas = dic["ptablas"]
        engine_rival.ppierde = dic["ppierde"]
        engine_rival.alias = dic["alias"]

        minutos = dic["minutos"]
        seconds = dic["seconds"]

        self.base_inicio(engine_rival, minutos, seconds, human_side=dic.get("human_side"))

        self.game.restore(dic["game_save"])

        self.vtime[WHITE].restore(dic["time_white"])
        self.vtime[BLACK].restore(dic["time_black"])

        self.goto_end()

    def adjourn(self):
        if QTUtil2.pregunta(self.main_window, _("Do you want to adjourn the game?")):
            dic = self.save_state()

            # se guarda en una bd Adjournments dic key = fecha y hora y tipo
            label_menu = _("Tourney-Elo") + ". " + self.engine_rival.name

            self.state = ST_ENDGAME

            with Adjournments.Adjournments() as adj:
                adj.add(self.game_type, dic, label_menu)
                adj.si_seguimos(self)

    def run_adjourn(self, dic):
        self.restore_state(dic)
        self.check_boards_setposition()
        self.start_message()
        self.show_clocks()
        self.play_next_move()

    def final_x(self):
        return self.rendirse()

    def rendirse(self):
        if self.state == ST_ENDGAME:
            return True
        if (len(self.game) > 0) and not self.pte_tool_resigndraw:
            if not QTUtil2.pregunta(
                self.main_window, _("Do you want to resign?") + " (%d)" % self.engine_rival.ppierde
            ):
                return False  # no abandona
            self.game.resign(self.human_side)
            self.show_result()
        else:
            self.procesador.start()

        return False

    def play_next_move(self):

        if self.state == ST_ENDGAME:
            return

        self.state = ST_PLAYING

        self.human_is_playing = False
        self.put_view()
        is_white = self.game.last_position.is_white

        if self.game.is_finished():
            self.show_result()
            return

        siRival = is_white == self.is_engine_side_white
        self.set_side_indicator(is_white)

        self.refresh()

        if siRival:
            self.start_clock(False)
            self.thinking(True)
            self.disable_all()

            siEncontrada = False

            if self.book:
                if self.game.last_position.num_moves >= self.maxMoveBook:
                    self.book = None
                else:
                    fen = self.last_fen()
                    pv = self.book.eligeJugadaTipo(fen, "au" if len(self.game) > 2 else "ap")
                    if pv:
                        rm_rival = EngineResponse.EngineResponse("Opening", self.is_engine_side_white)
                        rm_rival.from_sq = pv[:2]
                        rm_rival.to_sq = pv[2:4]
                        rm_rival.promotion = pv[4:]
                        siEncontrada = True
                    else:
                        self.book = None
            if not siEncontrada:
                tiempoBlancas = self.vtime[True].pending_time
                tiempoNegras = self.vtime[False].pending_time
                mrm = self.xrival.play_time_tourney(self.game, tiempoBlancas, tiempoNegras, self.secs_move)
                if mrm is None:
                    self.thinking(False)
                    return False
                rm_rival = mrm.mejorMov()

            self.stop_clock(False)

            self.thinking(False)
            if self.play_rival(rm_rival):
                self.lirm_engine.append(rm_rival)
                if self.valoraRMrival():
                    self.play_next_move()
                else:
                    if self.game.is_finished():
                        self.show_result()
                        return
            else:
                self.game.set_termination(TERMINATION_RESIGN, RS_WIN_PLAYER)
                self.show_result()
                return
        else:
            self.start_clock(True)

            self.human_is_playing = True
            self.activate_side(is_white)

    def player_has_moved(self, from_sq, to_sq, promotion=""):
        move = self.check_human_move(from_sq, to_sq, promotion)
        if not move:
            return False

        self.move_the_pieces(move.liMovs)
        self.stop_clock(True)

        self.add_move(move, True)
        self.play_next_move()
        return True

    def add_move(self, move, siNuestra):

        self.game.add_move(move)
        self.check_boards_setposition()

        self.put_arrow_sc(move.from_sq, move.to_sq)
        self.beepExtendido(siNuestra)

        self.pgnRefresh(self.game.last_position.is_white)
        self.refresh()

        if self.pte_tool_resigndraw:
            if len(self.game) > self.maxPlyRendirse:
                self.pte_tool_resigndraw = False
                self.pon_toolbar()

    def play_rival(self, engine_response):
        from_sq = engine_response.from_sq
        to_sq = engine_response.to_sq

        promotion = engine_response.promotion

        ok, mens, move = Move.get_game_move(self.game, self.game.last_position, from_sq, to_sq, promotion)
        if ok:
            self.add_move(move, False)
            self.move_the_pieces(move.liMovs, True)

            self.error = ""

            return True
        else:
            self.error = mens
            return False

    def show_result(self):
        if self.showed_result:  # Problema doble asignacion de ptos Thomas
            return
        self.state = ST_ENDGAME
        self.disable_all()
        self.human_is_playing = False
        self.main_window.stop_clock()

        mensaje, beep, player_win = self.game.label_resultado_player(self.human_side)

        self.beepResultado(beep)
        self.autosave()
        QTUtil.refresh_gui()

        elo = self.configuration.miceloActivo()
        relo = self.engine_rival.elo
        if player_win:
            difelo = self.engine_rival.pgana

        elif self.game.is_draw():
            difelo = self.engine_rival.ptablas

        else:
            difelo = self.engine_rival.ppierde

        nelo = elo + difelo
        if nelo < 0:
            nelo = 0
        self.configuration.ponMiceloActivo(nelo)

        rnelo = relo - difelo
        if rnelo < 100:
            rnelo = 100
        dme = DicMicElos()
        dme.cambia_elo(self.engine_rival.alias, rnelo)
        # TODO en el mensaje poner el elo con el que queda el rival, self.rival incluye el elo antiguo, hay que indicar el elo nuevo

        self.historial(elo, nelo)
        self.configuration.graba()

        mensaje += "\n\n%s : %d\n" % (_("New Tourney-Elo"), nelo)

        self.showed_result = True
        self.mensajeEnPGN(mensaje)
        self.ponFinJuego()

    def historial(self, elo, nelo):
        dic = {}
        dic["FECHA"] = datetime.datetime.now()
        dic["RIVAL"] = self.engine_rival.name
        dic["RESULTADO"] = self.resultado
        dic["AELO"] = elo
        dic["NELO"] = nelo

        lik = UtilSQL.ListSQL(self.configuration.fichEstadMicElo)
        lik.append(dic)
        lik.close()

        dd = UtilSQL.DictSQL(self.configuration.fichEstadMicElo, tabla="color")
        key = self.engine_rival.name
        dd[key] = self.human_side
        dd.close()

    def determinaColor(self, engine_rival):
        key = engine_rival.name

        dd = UtilSQL.DictSQL(self.configuration.fichEstadMicElo, tabla="color")
        previo = dd.get(key, random.randint(0, 1) == 0)
        dd.close()
        return not previo

    def set_clock(self):
        if self.state != ST_PLAYING:
            return

        def mira(is_white):
            ot = self.vtime[is_white]

            eti, eti2 = ot.etiquetaDif2()
            if eti:
                if is_white:
                    self.main_window.set_clock_white(eti, eti2)
                else:
                    self.main_window.set_clock_black(eti, eti2)

            if ot.time_is_consumed():
                self.game.set_termination_time()
                self.show_result()
                return False

            return True

        if Code.eboard:
            Code.eboard.writeClocks(self.vtime[True].label_dgt(), self.vtime[False].label_dgt())

        if self.human_is_playing:
            is_white = self.human_side
        else:
            is_white = not self.human_side
        return mira(is_white)

    def start_clock(self, siUsuario):
        self.vtime[siUsuario == self.human_side].start_marker()
        self.main_window.start_clock(self.set_clock, transicion=1000)

    def stop_clock(self, siUsuario):
        self.main_window.stop_clock()
        self.vtime[siUsuario == self.human_side].stop_marker(self.secs_move)
        self.set_clock()
        self.show_clocks()
        self.refresh()

    def show_clocks(self):
        if Code.eboard:
            Code.eboard.writeClocks(self.vtime[True].label_dgt(), self.vtime[False].label_dgt())

        for is_white in (WHITE, BLACK):
            ot = self.vtime[is_white]

            eti, eti2 = ot.etiquetaDif2()
            if eti:
                if is_white:
                    self.main_window.set_clock_white(eti, eti2)
                else:
                    self.main_window.set_clock_black(eti, eti2)
