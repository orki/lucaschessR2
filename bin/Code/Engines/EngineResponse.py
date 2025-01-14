import random
import time

import Code
from Code.Base import Game, Position
from Code.Base.Constantes import (
    ADJUST_BETTER,
    ADJUST_WORST_MOVE,
    ADJUST_WORSE,
    ADJUST_SOMEWHAT_WORSE_LESS_LESS,
    ADJUST_SOMEWHAT_WORSE_LESS,
    ADJUST_SOMEWHAT_BETTER_MORE_MORE,
    ADJUST_SOMEWHAT_BETTER_MORE,
    ADJUST_SOMEWHAT_BETTER,
    ADJUST_SIMILAR,
    ADJUST_LOW_LEVEL,
    ADJUST_INTERMEDIATE_LEVEL,
    ADJUST_HIGH_LEVEL,
    NO_RATING,
    INTERESTING_MOVE,
    GOOD_MOVE,
    VERY_GOOD_MOVE,
)


class EngineResponse:
    def __init__(self, name, si_blancas):
        self.name = name
        self.mate = 0
        self.puntos = 0
        self.sinMovimientos = False  # o por jaquemate o por ahogado
        self.pv = "a1a1"
        self.from_sq = ""
        self.to_sq = ""
        self.promotion = ""
        self.depth = 0
        self.time = 0
        self.nodes = 0
        self.nps = 0
        self.seldepth = 0
        self.is_white = si_blancas

        self.vtime = 0

        self.max_time = 0

        self.sinInicializar = True

    def save(self):
        li = [
            self.mate,
            self.puntos,
            self.pv,
            self.from_sq,
            self.to_sq,
            self.promotion,
            self.depth,
            self.nodes,
            self.nps,
            self.seldepth,
        ]
        return li

    def restore(self, li):
        (
            self.mate,
            self.puntos,
            self.pv,
            self.from_sq,
            self.to_sq,
            self.promotion,
            self.depth,
            self.nodes,
            self.nps,
            self.seldepth,
        ) = li
        self.sinInicializar = False

    def movimiento(self):
        return self.from_sq + self.to_sq + self.promotion.lower()

    def getPV(self):
        if self.pv == "a1a1" or not self.pv:
            return self.movimiento()
        return self.pv.strip().lower()

    def change_side(self, posicionAnterior=None):
        # Se usa en tutor para analizar las num_moves siguientes a la del usuario
        # Si no encuentra ninguna move y la move previa es jaque, pasa a mate en 1
        if posicionAnterior and self.sinMovimientos:
            if posicionAnterior.is_check():
                self.mate = 1
                return
        self.puntos = -self.puntos
        if self.mate:
            self.mate = -self.mate
            if self.mate > 0:
                self.mate += 1
        self.is_white = not self.is_white

    def siMejorQue(self, otra, control_difpts=0, control_difporc=0):
        if self.mate:
            if otra.mate < 0:
                if self.mate < 0:
                    return self.mate < otra.mate
                else:
                    return True
            elif otra.mate > 0:
                if self.mate < 0:
                    return False
                else:
                    return self.mate < otra.mate
            else:
                return self.mate > 0
        elif otra.mate:
            return otra.mate < 0
        dif = self.puntos - otra.puntos
        if dif <= 0:
            return False
        if control_difpts:
            if dif <= control_difpts:
                return False
        if control_difporc:
            control = int(abs(self.puntos) * control_difporc / 100)
            if dif < control:
                return False
        return True

    def ponBlunder(self, pts_dif):
        self.nvBlunder = pts_dif

    def nivelBlunder(self):
        return getattr(self, "nvBlunder", 0)

    def centipawns_abs(self):
        if self.mate:
            if self.mate < 0:
                puntos = -30000 - (self.mate + 1) * 10
            else:
                puntos = +30000 - (self.mate - 1) * 10
        else:
            puntos = self.puntos

        return puntos

    def score_abs5(self):
        if self.mate:
            if self.mate < 0:
                puntos = -30000 - (self.mate + 1) * 100
            else:
                puntos = +30000 - (self.mate - 1) * 100
        else:
            puntos = self.puntos

        return puntos

    def texto_rival(self):
        if self.mate:
            t = self.is_white if self.mate > 0 else not self.is_white
            mate = self.mate
            if mate < 0:
                mate += 1
            elif mate > 0:
                mate -= 1
            if -1 < mate < 1:
                d = {False: _("White is in checkmate"), True: _("Black is in checkmate")}
            else:
                d = {True: _("White mates in %1"), False: _("Black mates in %1")}
            return _X(d[t], str(abs(mate)))
        else:
            return self.texto()

    def texto(self):
        if self.mate:
            mt = self.mate
            if mt == 1:
                if self.is_white:
                    return _("Black is in checkmate")
                else:
                    return _("White is in checkmate")
            if mt == 1:
                if self.is_white:
                    return _X(_("White mates in %1"), 1)
                else:
                    return _X(_("Black mates in %1"), 1)
            if not self.is_white:
                mt = -mt
            if (mt > 1) and self.is_white:
                mt -= 1
            elif (mt < -1) and not self.is_white:
                mt += 1
            d = {True: _("White mates in %1"), False: _("Black mates in %1")}
            if self.mate > 0:
                t = self.is_white
            else:
                t = not self.is_white
            return _X(d[t], str(abs(mt)))

        else:
            pt = self.puntos
            if not self.is_white:
                pt = -pt
            cp = "%+0.2f" % (pt / 100.0)
            return "%s %s" % (cp, _("pawns"))

    def abrTexto(self):
        c = self.abrTextoBase()
        if self.mate == 0:
            c = "%s %s" % (c, _("pws"))
        return c

    def abrTextoPDT(self):
        c = self.abrTextoBase()
        if self.depth:
            c += "/%d" % self.depth
        if self.time:
            c += '/%0.01f"' % (self.time / 1000.0,)
        return c

    def abrTextoBase(self):
        if self.mate != 0:
            mt = self.mate
            if mt == 1:
                return ""
            if not self.is_white:
                mt = -mt
            if (mt > 1) and self.is_white:
                mt -= 1
            elif (mt < -1) and not self.is_white:
                mt += 1

            return "M%+d" % mt
        else:
            pts = self.puntos
            if not self.is_white:
                pts = -pts
            return "%+0.2f" % (pts / 100.0)

    def copia(self):
        rm = EngineResponse(self.name, self.is_white)
        rm.restore(self.save())
        return rm


st_uci_claves = {
    "multipv",
    "depth",
    "seldepth",
    "score",
    "time",
    "nodes",
    "pv",
    "hashfull",
    "tbhits",
    "nps",
    "currmove",
    "currmovenumber",
    "cpuload",
    "string",
    "refutation",
    "currline",
}


class MultiEngineResponse:
    name: str
    is_white: bool
    li_lem: list
    vtime: int
    depth: int
    max_time: int
    max_depth: int
    dicDepth: dict
    dicMultiPV: dict
    li_rm: list
    saveLines: bool
    lines: list
    _init_time_working: float
    cache_bound: dict
    game: Game
    fenBase: str

    def __init__(self, name, is_white):
        self.name = name
        self.is_white = is_white
        self.li_rm = []

        self.reset()
        self._init_time_working = time.time()

    def reset(self):
        self.vtime = 0
        self.depth = 0

        self.max_time = 0
        self.max_depth = 0

        self.dicDepth = {}
        self.dicMultiPV = {}
        self.li_rm = []

        self.saveLines = False
        self.lines = []
        self._init_time_working = time.time()

        self.cache_bound = {}

    def time_used(self):
        return time.time() - self._init_time_working

    def save(self):
        self.ordena()
        dic = {
            "name": self.name,
            "is_white": self.is_white,
            "vtime": self.vtime,
            "depth": self.depth,
            "max_time": self.max_time,
            "max_depth": self.max_depth,
            "li_rm": [rm.save() for rm in self.li_rm],
        }
        return dic

    def restore(self, dic):
        self.name = dic["name"]
        self.is_white = dic["is_white"]
        self.vtime = dic["vtime"]
        self.depth = dic["depth"]
        self.max_time = dic["max_time"]
        self.max_depth = dic["max_depth"]
        for num, sv in enumerate(dic["li_rm"]):
            rm = EngineResponse(self.name, self.is_white)
            rm.restore(sv)
            self.dicMultiPV[str(num + 1)] = rm
            self.li_rm.append(rm)

    def save_lines(self):
        self.saveLines = True
        self.lines = []

    def set_time_depth(self, max_time, max_depth):
        self.max_time = max_time
        self.max_depth = max_depth

    def dispatch(self, linea):
        is_bound = False
        if "bound" in linea and ("lowerbound" in linea or "upperbound" in linea):
            if "multipv" not in linea:
                return
            is_bound = True

        if linea.startswith("info ") and " pv " in linea:
            self.check_pv(linea[5:], is_bound)

        elif linea.startswith("bestmove"):
            self.check_best_move(linea)

        elif linea.startswith("info ") and " score " in linea:
            self.check_score(linea[5:])

        if self.saveLines:
            self.lines.append(linea)

    # def dispatchPV(self, pv):
    #     self.dispatch("info depth 1 score cp 0 time 1 pv %s" % pv)
    #     self.dispatch("bestmove %s" % pv)
    #     self.ordena()

    def ordena(self):
        li = []
        set_ya = set()
        dic = self.dicMultiPV
        keys = list(dic.keys())
        keys.sort(key=lambda xk: int(xk))
        for k in keys:
            rm = dic[k]
            mov = rm.movimiento()
            if not (mov in set_ya) and mov:
                set_ya.add(mov)
                li.append(rm)
        self.li_rm = sorted(li, key=lambda xrm: -xrm.centipawns_abs())  # de mayor a menor

    def __len__(self):
        return len(self.li_rm)

    def getTime(self):
        if len(self.li_rm):
            return self.li_rm[0].time
        return 0

    def check_pv(self, pv_base, is_bound):
        d_claves = self.check_claves(pv_base, st_uci_claves)

        if "pv" in d_claves:
            pv = d_claves["pv"].strip()
            if not pv:
                return
        else:
            return

        if "nodes" in d_claves:  # Toga en multipv, envia 0 si no tiene nada que contar
            if (d_claves["nodes"] == "0") and not ("mate" in pv_base):
                return

        if "score" in d_claves:
            if "mate 0 " in pv_base or "mate -0 " in pv_base or "mate +0 " in pv_base:
                return

        if "multipv" in d_claves:
            k_multi = d_claves["multipv"]
            if not (k_multi in self.dicMultiPV):
                self.dicMultiPV[k_multi] = EngineResponse(self.name, self.is_white)
        else:
            if len(self.dicMultiPV) == 0:
                k_multi = "1"
                self.dicMultiPV[k_multi] = EngineResponse(self.name, self.is_white)
            else:
                k_multi = list(self.dicMultiPV.keys())[0]

        rm = self.dicMultiPV[k_multi]
        rm.sinInicializar = False

        if "depth" in d_claves:
            depth = int(d_claves["depth"].strip())
            if self.max_depth:
                if rm.from_sq:  # Es decir que ya tenemos datos (rm.pv al principio = a1a1
                    if (depth > self.max_depth) and (depth > rm.depth):
                        return
            rm.depth = depth
        else:
            depth = 0

        if "time" in d_claves:
            rm.time = int(d_claves["time"].strip())

        if "nodes" in d_claves:
            rm.nodes = int(d_claves["nodes"].strip())

        if "nps" in d_claves:
            nps = d_claves["nps"].strip()
            if " " in nps:
                nps = nps.split(" ")[0]
            if nps.isdigit():
                rm.nps = int(nps)

        if "seldepth" in d_claves:
            rm.seldepth = int(d_claves["seldepth"].strip())

        if "score" in d_claves:
            score = d_claves["score"].strip()
            if score.startswith("cp "):
                rm.puntos = int(score.split(" ")[1])
                rm.mate = 0
                rm.sinMovimientos = False
            elif score.startswith("mate "):
                rm.puntos = 0
                rm.mate = int(score.split(" ")[1])
                rm.sinMovimientos = False

        pv = d_claves["pv"].strip()
        x = pv.find(" ")
        pv1 = pv[:x] if x >= 0 else pv
        rm.pv = pv
        rm.from_sq = pv1[:2]
        rm.to_sq = pv1[2:4]
        rm.promotion = pv1[4].lower() if len(pv1) == 5 else ""

        if is_bound:
            if pv1 in self.cache_bound:
                pv_prop = self.cache_bound[pv1]
                if pv_prop.startswith(pv):
                    rm.pv = pv_prop
        else:
            self.cache_bound[pv1] = pv

        if depth:
            if depth not in self.dicDepth:
                self.dicDepth[depth] = {}
            self.dicDepth[depth][rm.movimiento()] = rm.score_abs5()

    def check_score(self, pv_base):
        d_claves = self.check_claves(pv_base, st_uci_claves)

        if "multipv" in d_claves:
            k_multi = d_claves["multipv"]
            if not (k_multi in self.dicMultiPV):
                self.dicMultiPV[k_multi] = EngineResponse(self.name, self.is_white)
        else:
            if len(self.dicMultiPV) == 0:
                k_multi = "1"
                self.dicMultiPV[k_multi] = EngineResponse(self.name, self.is_white)
            else:
                k_multi = list(self.dicMultiPV.keys())[0]

        rm = self.dicMultiPV[k_multi]
        rm.sinInicializar = False

        if "depth" in d_claves:
            depth = d_claves["depth"].strip()
            if depth.isdigit():
                depth = int(depth)
                if self.max_depth:
                    if rm.from_sq:  # Es decir que ya tenemos datos (rm.pv al principio = a1a1
                        if (depth > self.max_depth) and (depth > rm.depth):
                            return
                rm.depth = depth

        if "time" in d_claves:
            tm = d_claves["time"].strip()
            if tm.isdigit():
                rm.time = int(tm)

        score = d_claves["score"].strip()
        if score.startswith("cp "):
            rm.puntos = int(score.split(" ")[1])
            rm.mate = 0
            rm.sinMovimientos = False
        elif score.startswith("mate "):
            rm.puntos = 0
            rm.mate = int(score.split(" ")[1])
            if not rm.mate:  # stockfish mate 0
                rm.mate = -1

    def add_rm(self, rm):
        # Para los analysis MultiPV donde no han considerado una move
        max_depth = 0
        included = False
        for cdepth, rm1 in self.dicMultiPV.items():
            if rm.movimiento() == rm1.movimiento():
                included = True
                break
            if int(cdepth) > max_depth:
                max_depth = int(cdepth)
        if not included:
            self.dicMultiPV[str(max_depth + 1)] = rm
        self.ordena()
        for pos, rm1 in enumerate(self.li_rm):
            if rm1.movimiento() == rm.movimiento():
                return pos

    def check_best_move(self, bestmove):
        if len(self.dicMultiPV) > 1:
            return

        rm = self.dicMultiPV.get("1", EngineResponse(self.name, self.is_white))

        # rm = EngineResponse( self.name, self.is_white )
        self.dicMultiPV = {"1": rm}

        rm.sinInicializar = False
        d_claves = self.check_claves(bestmove, {"bestmove", "ponder"})
        rm.from_sq = ""
        rm.to_sq = ""
        rm.promotion = ""
        rm.sinMovimientos = False
        if "bestmove" in d_claves:
            bestmove = d_claves["bestmove"].strip()
            rm.sinMovimientos = True
            if bestmove:
                if len(bestmove) >= 4:

                    def bien(a8):
                        return a8[0] in "abcdefgh" and a8[1] in "12345678"

                    d = bestmove[:2]
                    h = bestmove[2:4]

                    if bien(d) and bien(h):
                        rm.sinMovimientos = d == h
                        rm.from_sq = d
                        rm.to_sq = h
                        if len(bestmove) == 5 and bestmove[4].lower() in "qbrn":
                            rm.promotion = bestmove[4].lower()
                        if rm.pv == "a1a1":  # No muestra pvs solo directamente
                            rm.pv = bestmove

        else:
            rm.sinMovimientos = True

    def check_claves(self, mensaje, st_claves):
        d_claves = {}
        key = ""
        dato = ""
        for palabra in mensaje.split(" "):
            if palabra in st_claves:
                if key:
                    d_claves[key] = dato.strip()
                key = palabra
                dato = ""
            else:
                dato += " " + palabra
        if key:
            d_claves[key] = dato.strip()
        return d_claves

    def is_stable(self, centipawns, num_depths):
        li_depths = list(self.dicDepth.keys())
        if len(li_depths) > 40:
            return True
        if len(li_depths) <= num_depths:
            return False
        li_depths.sort(reverse=True)

        def best(npos):
            dic = self.dicDepth[li_depths[npos]]
            li_best = []
            pmax = -999999
            for mov, pts in dic.items():
                if pts > pmax:
                    li_best = [mov]
                    pmax = pts
                elif pts == pmax:
                    li_best.append(mov)
            return li_best, pmax

        def equal(li_best0, li_best1):
            li_mov0, pts0 = li_best0
            li_mov1, pts1 = li_best1
            if len(li_mov0) != len(li_mov1):
                return False
            if abs(pts0 - pts1) > centipawns:
                return False

            for mov0 in li_mov0:
                if not (mov0 in li_mov1):
                    return False
            return True

        l_d = [best(pos) for pos in range(num_depths)]
        l_0 = l_d[0]
        for pos in range(1, num_depths):
            if not equal(l_d[pos], l_0):
                return False
        return True

    def mejorRMQue(self, rm, difpts, difporc):
        if self.li_rm:
            return self.li_rm[0].siMejorQue(rm, difpts, difporc)
        else:
            return False

    def buscaRM(self, movimiento):
        movimiento = movimiento.lower()
        for n, rm in enumerate(self.li_rm):
            if rm.movimiento() == movimiento:
                return rm, n
        return None, -1

    def contain(self, movimiento):
        movimiento = movimiento.lower()
        for n, rm in enumerate(self.li_rm):
            if rm.movimiento() == movimiento:
                return True
        return False

    def mejorMovQue(self, movimiento):
        if self.li_rm:
            rm, n = self.buscaRM(movimiento)
            if rm is None:
                return True
            if n == 0:
                return False
            return self.li_rm[0].siMejorQue(rm)
        return False

    def numMejorMovQue(self, movimiento):
        rm, n = self.buscaRM(movimiento)
        num = len(self.li_rm)
        if rm is None:
            return num
        x = 0
        for rm1 in self.li_rm:
            if rm1.siMejorQue(rm):
                x += 1
        return x

    def rmBest(self):
        num = len(self.li_rm)
        if num == 0:
            return None
        rm = self.li_rm[0]
        for x in range(1, num):
            rm1 = self.li_rm[x]
            if rm1.siMejorQue(rm):
                rm = rm1
        return rm

    def difPointsBest(self, movimiento):
        rmbest = self.rmBest()
        if not rmbest:
            return 0, 0
        pbest = rmbest.score_abs5()
        rm, n = self.buscaRM(movimiento)
        if rm is None:
            return pbest, 0
        return pbest, rm.score_abs5()

    def mejorMov(self):
        if self.li_rm:
            return self.li_rm[0]
        return EngineResponse(self.name, self.is_white)

    def bestmoves(self):
        li = []
        if not self.li_rm:
            return li
        n = len(self.li_rm)
        rm0 = self.li_rm[0]
        li.append(rm0)
        if n > 1:
            for n in range(1, n):
                rm = self.li_rm[n]
                if rm0.centipawns_abs() == rm.centipawns_abs():
                    li.append(rm)
                else:
                    break
        return li

    def is_pos_bestmove(self, pos):
        if pos == 0:
            return True
        cp0 = self.li_rm[0].centipawns_abs()
        cpuser = self.li_rm[pos].centipawns_abs()
        return cp0 == cpuser

    def getdepth0(self):
        return self.li_rm[0].depth if self.li_rm else 0

    def mejorMovDetectaBlunders(self, fdbg, mindifpuntos, maxmate):
        rm0 = self.li_rm[0]
        if maxmate:
            if 0 < rm0.mate <= maxmate:
                if fdbg:
                    fdbg.write("1. %s : %s %d <= %d\n" % (rm0.pv, _("Mate"), rm0.mate, maxmate))
                return True
        if mindifpuntos:
            game_base = self.game  # asignada por el engine_manager
            num_moves = game_base.num_moves()
            puntos_previos = 0
            if num_moves >= 3:
                move = game_base.move(num_moves - 3)
                if hasattr(move, "puntosABS_3"):  # se graban en mejormovajustado
                    puntos_previos = move.puntosABS_3
            difpuntos = (
                    rm0.centipawns_abs() - puntos_previos
            )  # son puntos ganados por el engine y perdidos por el player
            if difpuntos > mindifpuntos:
                if fdbg:
                    fdbg.write("1. %s : %s %d > %d\n" % (rm0.pv, _("Centipawns lost"), difpuntos, mindifpuntos))
                return True
        return False

    def ajustaPersonalidad(self, una):
        def x(key):
            return una.get(key, 0)

        cp = Position.Position()
        cp.read_fen(self.fenBase)

        dbg = x("DEBUG")
        if dbg:
            fdbg = open(dbg, "at", encoding="utf-8", errors="ignore")
            fdbg.write("\n%s\n" % cp.pr_board())
            dpr = _("In the expected moves")
        else:
            fdbg = None
            dpr = None

        # Aterrizaje
        aterrizaje = una.get("ATERRIZAJE", 50)

        # Blunders
        mindifpuntos = x("MINDIFPUNTOS")
        maxmate = x("MAXMATE")
        if self.mejorMovDetectaBlunders(fdbg, mindifpuntos, maxmate):
            if fdbg:
                fdbg.close()
            return ADJUST_BETTER, mindifpuntos, maxmate, dbg, aterrizaje

        # Comprobamos donde estamos, si medio o final
        tipo = "F" if len(cp) <= x("MAXPIEZASFINAL") else ""

        # Variable a analizar
        x_mpn = x("MOVERPEON" + tipo)
        x_apz = x("AVANZARPIEZA" + tipo)
        x_j = x("JAQUE" + tipo)
        x_c = x("CAPTURAR" + tipo)

        x2_b = x("2BPR" + tipo)
        x_av_pr = x("AVANZARPR" + tipo)
        x_jpr = x("JAQUEPR" + tipo)
        x_cpr = x("CAPTURARPR" + tipo)

        # Miramos todas las propuestas
        for num, rm in enumerate(self.li_rm):
            game = Game.Game(cp)
            game.read_pv(rm.pv)
            jg0 = game.move(0)
            ps0 = game.first_position
            ps_z = game.last_position

            if dbg:
                pgn = ""
                si = False
                for move in game.li_moves:
                    pgn += move.pgnEN() + " "
                    if si:
                        pgn += "- "
                    si = not si
                pgn = pgn.strip("- ")

                if rm.mate:
                    fdbg.write("%2d; %s ; %d %s\n" % (num + 1, pgn, rm.mate, _("Mate")))
                else:
                    # fdbg.write( "%2d. %s : %d\n"%(num+1,pgn,rm.puntos) )
                    fdbg.write("%2d; %s; %d\n" % (num + 1, pgn, rm.puntos))

            if rm.mate:
                continue

            if x_mpn:
                if ps0.squares.get(jg0.from_sq, "").lower() == "p":
                    rm.puntos += x_mpn
                    if dbg:
                        fdbg.write("    %s : %d -> %d\n" % (_("To move a pawn"), x_mpn, rm.puntos))

            if x_apz:
                if ps0.squares.get(jg0.from_sq, "").lower() != "p":
                    if tipo == "F":
                        dif = ps0.distanciaPiezaKenemigo(jg0.from_sq) - ps0.distanciaPiezaKenemigo(jg0.to_sq)
                    else:
                        nd = int(jg0.from_sq[1])
                        nh = int(jg0.to_sq[1])
                        dif = nh - nd
                        if not ps0.is_white:
                            dif = -dif
                    if dif > 0:
                        rm.puntos += x_apz
                        if dbg:
                            fdbg.write("    %s : %d -> %d\n" % (_("Advance piece"), x_apz, rm.puntos))

            if x_j:
                if jg0.is_check:
                    rm.puntos += x_j
                    if dbg:
                        fdbg.write("    %s : %d -> %d\n" % (_("Make check"), x_j, rm.puntos))

            if x_c:
                if jg0.siCaptura():
                    rm.puntos += x_c
                    if dbg:
                        fdbg.write("    %s : %d -> %d\n" % (_("Capture"), x_j, rm.puntos))

            if x2_b:
                if ps_z.numPiezas("") == 2:
                    rm.puntos += x2_b
                    if dbg:
                        fdbg.write("    %s : %d -> %d \n" % (_("Keep the two bishops"), x2_b, rm.puntos))

            if x_av_pr:
                p_z = ps_z.pesoWB()
                p0 = ps0.pesoWB()
                valor_wb = p_z - p0
                if not cp.is_white:
                    valor_wb = -valor_wb
                if valor_wb > 0:
                    rm.puntos += x_av_pr
                    if dbg:
                        if not cp.is_white:
                            p0 = -p0
                            p_z = -p_z
                        fdbg.write(
                            "    %s (%s) : %d -> %d [%d ≥ %d]\n" % (_("Advance"), dpr, x_av_pr, rm.puntos, p0, p_z))

            if x_jpr:
                n = True
                for move in game.li_moves:
                    if n and move.is_check:
                        rm.puntos += x_jpr
                        if dbg:
                            fdbg.write("    %s (%s) : %d -> %d\n" % (_("Make check"), dpr, x_jpr, rm.puntos))
                        break
                    n = not n

            if x_cpr:
                n = True
                for move in game.li_moves:
                    if n and move.siCaptura():
                        rm.puntos += x_cpr
                        if dbg:
                            fdbg.write("    %s (%s) : %d -> %d\n" % (_("Capture"), dpr, x_cpr, rm.puntos))
                        break
                    n = not n

        # Ordenamos
        li = []
        for rm in self.li_rm:
            elpeor = True
            for n, rm1 in enumerate(li):
                if rm.siMejorQue(rm1, 0, 0):
                    li.insert(n, rm)
                    elpeor = False
                    break
            if elpeor:
                li.append(rm)
        self.li_rm = li

        if dbg:
            fdbg.write("Result :\n")
            for num, rm in enumerate(self.li_rm):
                game = Game.Game(cp)
                game.read_pv(rm.pv)

                pgn = ""
                si = False
                for move in game.li_moves:
                    pgn += move.pgnEN() + " "
                    if si:
                        pgn += "- "
                    si = not si
                pgn = pgn.strip("- ")

                if rm.mate:
                    fdbg.write("%d. %s : %d %s\n" % (num + 1, pgn, rm.mate, _("Mate")))
                else:
                    fdbg.write("%d. %s : %d\n" % (num + 1, pgn, rm.puntos))

            fdbg.write("\n")
            fdbg.close()

        return (
            una.get("AJUSTARFINAL" if tipo == "F" else "ADJUST", ADJUST_BETTER),
            mindifpuntos,
            maxmate,
            dbg,
            aterrizaje,
        )

    def mejorMovAjustadoNivel(self, nTipo):
        if nTipo == ADJUST_HIGH_LEVEL:
            dic = {
                ADJUST_BETTER: 60,
                ADJUST_SOMEWHAT_BETTER_MORE_MORE: 30,
                ADJUST_SOMEWHAT_BETTER_MORE: 15,
                ADJUST_SOMEWHAT_BETTER: 10,
                ADJUST_SIMILAR: 5,
            }
        elif nTipo == ADJUST_INTERMEDIATE_LEVEL:
            dic = {
                ADJUST_SOMEWHAT_BETTER_MORE_MORE: 5,
                ADJUST_SOMEWHAT_BETTER_MORE: 10,
                ADJUST_SOMEWHAT_BETTER: 25,
                ADJUST_SIMILAR: 60,
                ADJUST_WORSE: 25,
                ADJUST_SOMEWHAT_WORSE_LESS: 10,
                ADJUST_SOMEWHAT_WORSE_LESS_LESS: 5,
            }
        elif nTipo == ADJUST_LOW_LEVEL:
            dic = {
                ADJUST_SIMILAR: 25,
                ADJUST_WORSE: 60,
                ADJUST_SOMEWHAT_WORSE_LESS: 25,
                ADJUST_SOMEWHAT_WORSE_LESS_LESS: 10,
            }
        else :
            dic = {}
        tp = 0
        for k, v in dic.items():
            tp += v
        sel = random.randint(1, tp)
        t = 0
        for k, v in dic.items():
            t += v
            if sel <= t:
                return k

    def mejorMovAjustadoBlundersNegativo(self, mindifpuntos, maxmate):
        rm0 = self.li_rm[0]
        if self.mejorMovDetectaBlunders(None, mindifpuntos, maxmate):
            return rm0
        if rm0.centipawns_abs() < -10:
            li = []
            for rm in self.li_rm:
                if rm.centipawns_abs() == rm0.centipawns_abs():
                    li.append(rm)
            if len(li) == 1:
                return rm0
            else:
                return random.choice(li)
        return None

    def mejorMovAjustadoSuperior(self, nivel, mindifpuntos, maxmate, aterrizaje):
        resp = self.mejorMovAjustadoBlundersNegativo(mindifpuntos, maxmate)
        if resp:
            return resp

        # Buscamos una move positiva que no sea de mate
        # Si no la hay, cogemos el ultimo
        rm_ini = None
        for rm in self.li_rm:
            if rm.mate == 0:
                rm_ini = rm
                break
        if rm_ini is None:
            return self.li_rm[-1]  # Mandamos el mate peor

        pts_ini = rm_ini.centipawns_abs()
        if pts_ini > aterrizaje:
            minimo = pts_ini - aterrizaje
        else:
            minimo = 0

        li = []
        for rm in self.li_rm:
            pts = rm.centipawns_abs()
            if pts < minimo:
                break
            li.append(rm)

        if not li:
            return self.li_rm[0]
        n_li = len(li)

        return li[0] if n_li < nivel else li[-nivel]

    def mejorMovAjustadoInferior(self, nivel, mindifpuntos, maxmate, aterrizaje):
        resp = self.mejorMovAjustadoBlundersNegativo(mindifpuntos, maxmate)
        if resp:
            return resp

        # Buscamos una move positiva que no sea de mate
        # Si no la hay, cogemos el ultimo
        rm_ini = None
        for rm in self.li_rm:
            if rm.mate == 0:
                rm_ini = rm
                break
        if rm_ini is None:
            return self.li_rm[-1]  # Mandamos el mate peor

        pts_ini = rm_ini.centipawns_abs()
        if pts_ini > aterrizaje:  # el engine hace una move bastante peor, pero no malisima
            minimo = pts_ini - aterrizaje
        else:
            minimo = 0

        li = []
        for rm_sel in self.li_rm:
            pts = rm_sel.centipawns_abs()
            if pts < minimo:
                li.append(rm_sel)
        if not li:
            return self.li_rm[-1]  # Mandamos la move peor
        n_li = len(li)

        return li[-1] if n_li < nivel else li[nivel - 1]

    def mejorMovAjustadoSimilar(self, mindifpuntos, maxmate, aterrizaje):
        resp = self.mejorMovAjustadoBlundersNegativo(mindifpuntos, maxmate)
        if resp:
            return resp

        # Buscamos una move positiva que no sea de mate
        # Si no la hay, cogemos el ultimo
        rm_ini = None
        for rm in self.li_rm:
            if rm.mate == 0:
                rm_ini = rm
                break
        if rm_ini is None:
            return self.li_rm[-1]  # Mandamos el mate peor

        pts_ini = rm_ini.centipawns_abs()
        if pts_ini > aterrizaje:  # el engine hace una move peor, pero no malisima
            minimo = pts_ini - aterrizaje
        else:
            minimo = 0

        rm_ant = self.li_rm[0]
        rm_sel = rm_ant
        pts_ant = rm_ant.centipawns_abs()
        for rm in self.li_rm:
            pts = rm.centipawns_abs()
            if pts < minimo:
                rm_sel = rm if abs(pts_ant) > abs(pts) else rm_ant
                break
            rm_ant = rm
            pts_ant = pts
        return rm_sel

    def best_adjusted_move(self, n_tipo):
        mindifpuntos = maxmate = 0
        if self.li_rm:
            rm_sel = None
            aterrizaje = 50
            si_personalidad = n_tipo >= 1000  # Necesario para grabar los puntos

            if si_personalidad:
                li_personalities = Code.configuration.li_personalities
                n_tipo, mindifpuntos, maxmate, dbg, aterrizaje = self.ajustaPersonalidad(
                    li_personalities[n_tipo - 1000]
                )

            if n_tipo == ADJUST_BETTER:
                rm_sel = self.li_rm[0]
            elif n_tipo == ADJUST_WORST_MOVE:
                rm_sel = self.li_rm[-1]
            elif n_tipo in (ADJUST_HIGH_LEVEL, ADJUST_LOW_LEVEL, ADJUST_INTERMEDIATE_LEVEL):
                n_tipo = self.mejorMovAjustadoNivel(n_tipo)  # Se corta el if para que se calcule el nTipo

            if n_tipo in (ADJUST_SOMEWHAT_BETTER, ADJUST_SOMEWHAT_BETTER_MORE, ADJUST_SOMEWHAT_BETTER_MORE_MORE):
                nivel = {ADJUST_SOMEWHAT_BETTER: 1, ADJUST_SOMEWHAT_BETTER_MORE: 2, ADJUST_SOMEWHAT_BETTER_MORE_MORE: 3}
                if not si_personalidad:
                    mindifpuntos, maxmate = 200, 2
                rm_sel = self.mejorMovAjustadoSuperior(nivel[n_tipo], mindifpuntos, maxmate, aterrizaje)

            elif n_tipo == ADJUST_SIMILAR:
                if not si_personalidad:
                    mindifpuntos, maxmate = 300, 1
                rm_sel = self.mejorMovAjustadoSimilar(mindifpuntos, maxmate, aterrizaje)

            elif n_tipo in (ADJUST_WORSE, ADJUST_SOMEWHAT_WORSE_LESS, ADJUST_SOMEWHAT_WORSE_LESS_LESS):
                nivel = {ADJUST_WORSE: 1, ADJUST_SOMEWHAT_WORSE_LESS: 2, ADJUST_SOMEWHAT_WORSE_LESS_LESS: 3}
                if not si_personalidad:
                    mindifpuntos, maxmate = 400, 1
                rm_sel = self.mejorMovAjustadoInferior(nivel[n_tipo], mindifpuntos, maxmate, aterrizaje)

            if rm_sel is None:
                rm_sel = self.li_rm[0]

            # Para comprobar perdida de puntos
            if len(self.game):
                self.game.last_jg().puntosABS_3 = rm_sel.centipawns_abs()

            return rm_sel
        return EngineResponse(self.name, self.is_white)

    def set_nag_color(self, rm):
        mj_pts = self.li_rm[0].centipawns_abs()
        rm_pts = rm.centipawns_abs()
        nb = mj_pts - rm_pts
        if nb > 5:
            ev = Code.analysis_eval.evaluate(self.li_rm[0], rm)
            return ev, ev

        libest = self.bestmoves()
        if not (rm in libest):
            return NO_RATING, NO_RATING

        # Si la mayoría son buenos movimientos
        if len(libest) * 1.0 / len(self.li_rm) >= 0.8:
            return NO_RATING, GOOD_MOVE

        # Si en la depth que se encontró era menor que 4
        dic = self.dicDepth
        if dic:
            li = list(dic.keys())
            li.sort()
            first_depth = 0
            mv = rm.movimiento()
            for depth in li:
                dic_depth = dic[depth]
                if mv in dic_depth:
                    pts = dic_depth[mv]
                    ok = True
                    for m, v in dic_depth.items():
                        if v > pts + 5:
                            ok = False
                            break
                    if ok:
                        first_depth = depth
                        break
            color = GOOD_MOVE
            if first_depth >= Code.configuration.x_eval_very_good_depth:
                if len(libest) == 1 and len(self.li_rm) > 1 and (mj_pts - self.li_rm[1].centipawns_abs()) > 70:
                    nag = VERY_GOOD_MOVE
                    color = VERY_GOOD_MOVE
                else:
                    nag = GOOD_MOVE
            elif first_depth >= Code.configuration.x_eval_good_depth:
                nag = GOOD_MOVE
            elif first_depth >= Code.configuration.x_eval_speculative_depth:
                nag = INTERESTING_MOVE
                color = INTERESTING_MOVE
            else:
                nag = NO_RATING
            return nag, color

        return NO_RATING, GOOD_MOVE
