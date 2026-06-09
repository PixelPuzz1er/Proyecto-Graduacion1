from core.commands.base_command import BaseCommand
from core.commands.line_cmd     import LineCommand
from core.commands.polyline_cmd import PolylineCommand
from core.commands.circle_cmd   import CircleCommand
from core.commands.circle2p_cmd import Circle2PCommand
from core.commands.circle3p_cmd import Circle3PCommand
from core.commands.arc_cmd      import ArcCommand
from core.commands.arcsce_cmd   import ArcSCECommand
from core.commands.arcsca_cmd   import ArcSCACommand
from core.commands.arcsel_cmd   import ArcSCLCommand
from core.commands.arsea_cmd    import ArcSEACommand
from core.commands.arser_cmd    import ArcSERCommand
from core.commands.arccse_cmd   import ArcCSECommand
from core.commands.arccsa_cmd   import ArcCSACommand
from core.commands.arccsl_cmd   import ArcCSLCommand
from core.commands.arcont_cmd   import ArcContinueCommand
from core.commands.rect_cmd     import RectCommand
from core.commands.ellipse_cmd  import EllipseCommand
from core.commands.polygon_cmd  import PolygonCommand
from core.commands.hatch_cmd    import HatchCommand
from core.commands.spline_cmd   import SplineCommand
from core.commands.xline_cmd    import XLineCommand
from core.commands.ray_cmd      import RayCommand
from core.commands.point_cmd    import PointCommand
from core.commands.erase_cmd    import EraseCommand
from core.commands.move_cmd     import MoveCommand
from core.commands.copy_cmd     import CopyCommand
from core.commands.rotate_cmd   import RotateCommand
from core.commands.scale_cmd    import ScaleCommand
from core.commands.trim_cmd     import TrimCommand, ExtendCommand
from core.commands.fillet_cmd   import FilletCommand
from core.commands.mirror_cmd   import MirrorCommand
from core.commands.stretch_cmd  import StretchCommand
from core.commands.offset_cmd   import OffsetCommand
from core.commands.explode_cmd  import ExplodeCommand
from core.commands.array_cmd    import ArrayCommand
from core.commands.chamfer_cmd  import ChamferCommand
from core.commands.join_cmd     import JoinCommand
from core.commands.break_cmd    import BreakCommand

COMMAND_MAP: dict[str, type[BaseCommand]] = {
    "L":       LineCommand,    "LINE":     LineCommand,
    "PL":      PolylineCommand,"PLINE":    PolylineCommand,
    "C":       CircleCommand,  "CIRCLE":   CircleCommand,
    "A":       ArcCommand,     "ARC":      ArcCommand,
    "REC":     RectCommand,    "RECTANG":  RectCommand,
    "EL":      EllipseCommand, "ELLIPSE":  EllipseCommand,
    "POL":     PolygonCommand, "POLYGON":  PolygonCommand,
    "H":       HatchCommand,   "HATCH":    HatchCommand,
    "C2P":     Circle2PCommand,
    "C3P":     Circle3PCommand,
    "ASCE":    ArcSCECommand,
    "ASCA":    ArcSCACommand,
    "ASCL":    ArcSCLCommand,
    "ASEA":    ArcSEACommand,
    "ASER":    ArcSERCommand,
    "ACSE":    ArcCSECommand,
    "ACSA":    ArcCSACommand,
    "ACSL":    ArcCSLCommand,
    "ACONT":   ArcContinueCommand,
    "SPL":     SplineCommand,  "SPLINE":   SplineCommand,
    "XL":      XLineCommand,   "XLINE":    XLineCommand,
    "RAY":     RayCommand,
    "PO":      PointCommand,   "POINT":    PointCommand,
    "E":       EraseCommand,   "ERASE":    EraseCommand,
    "M":       MoveCommand,    "MOVE":     MoveCommand,
    "CO":      CopyCommand,    "COPY":     CopyCommand,
    "RO":      RotateCommand,  "ROTATE":   RotateCommand,
    "SC":      ScaleCommand,   "SCALE":    ScaleCommand,
    "TR":      TrimCommand,    "TRIM":     TrimCommand,
    "EX":      ExtendCommand,  "EXTEND":   ExtendCommand,
    "F":       FilletCommand,  "FILLET":   FilletCommand,
    "MI":      MirrorCommand,  "MIRROR":   MirrorCommand,
    "S":       StretchCommand, "STRETCH":  StretchCommand,
    "O":       OffsetCommand,  "OFFSET":   OffsetCommand,
    "X":       ExplodeCommand, "EXPLODE":  ExplodeCommand,
    "AR":      ArrayCommand,   "ARRAY":    ArrayCommand,
    "CHA":     ChamferCommand, "CHAMFER":  ChamferCommand,
    "J":       JoinCommand,    "JOIN":     JoinCommand,
    "BR":      BreakCommand,   "BREAK":    BreakCommand,
}

COMMAND_ALIASES: dict[str, str] = {
    "L": "LINE", "LINEA": "LINE",
    "C": "CIRCLE", "CIRCULO": "CIRCLE",
    "REC": "RECTANG",
    "H": "HATCH", "SOMBREADO": "HATCH",
    "E": "ERASE", "BORRAR": "ERASE",
    "M": "MOVE", "MOVER": "MOVE",
    "CO": "COPY", "CP": "COPY",
    "RO": "ROTATE",
    "SC": "SCALE",
    "TR": "TRIM",
    "EX": "EXTEND",
    "MI": "MIRROR", "ESPEJO": "MIRROR",
    "S": "STRETCH", "ESTIRAR": "STRETCH",
    "O": "OFFSET", "DESFASE": "OFFSET",
    "X": "EXPLODE", "DESCOMPONER": "EXPLODE",
    "AR": "ARRAY",
    "CHA": "CHAMFER", "CHAFAN": "CHAMFER",
    "J": "JOIN", "JUNTAR": "JOIN",
    "BR": "BREAK", "PARTIR": "BREAK",
}

COMMAND_CLASS_MAP: dict[type, str] = {
    LineCommand: "L",
    PolylineCommand: "PL",
    CircleCommand: "C", Circle2PCommand: "C", Circle3PCommand: "C",
    ArcCommand: "A", ArcSCECommand: "A", ArcSCACommand: "A",
    ArcSCLCommand: "A", ArcSEACommand: "A", ArcSERCommand: "A",
    ArcCSECommand: "A", ArcCSACommand: "A", ArcCSLCommand: "A",
    ArcContinueCommand: "A",
    RectCommand: "REC", PolygonCommand: "REC",
    EllipseCommand: "EL",
    HatchCommand: "H",
    SplineCommand: "SPL",
    XLineCommand: "XL",
    RayCommand: "RAY",
    PointCommand: "PO",
    MoveCommand: "M",
    CopyCommand: "CO",
    RotateCommand: "RO",
    ScaleCommand: "SC",
    EraseCommand: "E",
    TrimCommand: "TR", ExtendCommand: "TR",
    FilletCommand: "F",
    MirrorCommand: "MI",
    StretchCommand: "S",
    OffsetCommand: "O",
    ExplodeCommand: "X",
    ArrayCommand: "AR",
    ChamferCommand: "CHA",
    JoinCommand: "J",
    BreakCommand: "BR",
}
