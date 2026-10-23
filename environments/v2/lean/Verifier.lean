import Lean
import NRBPrelude
open Lean Meta Elab

-- The only dynamically elaborated input is one term, never a command.
-- A small, published proof language excludes metaprogram execution and configs.
def safeTacticKinds : List String := [
  "tacticSorry", "tacticAdmit", "tacticTry_", "tacticRepeat_", "tacticNext_", "caseArg", "caseArgRename", "caseArgWild", "rcasesPat.ignore", "rcasesPat.clear", "rcasesPat.explicit",
  "elimTarget", "tacticHave_", "tacticLet_", "tacticShow_", "tacticRfl", "tacticTrivial", "locationType",
  "refine", "refine'", "left", "right", "rename", "classical", "match", "matchRhs", "matchAlts", "applyRfl", "acRfl", "symm", "congr", "calc", "paren", "nestedTactic", "simpaArgsRest", "simpArgsRest", "dsimpArgsRest", "simpAllArgsRest",
  "tacticSeq", "tacticSeq1Indented", "tacticSeqBracketed", "null",
  "intro", "intros", "exact", "apply", "assumption", "constructor",
  "rfl", "trivial", "contradiction", "omega", "decide",
  "simp", "simpAll", "simpa", "dsimp", "unfold", "rw", "rewriteSeq", "rwRuleSeq", "rwRule",
  "location", "locationHyp", "locationWildcard", "simpStar", "simpErase", "simpLemma",
  "simpOnly", "simpArgs", "simpErase", "optConfig", "optConfigItem", "optStar",
  "induction", "cases", "inductionAlts", "inductionAlt", "inductionAltsWhere",
  "inductionAltLHS", "inductionAltsWhere", "inductionTarget", "withArg",
  "rcases", "rcasesPat", "rcasesPat.tuple", "rcasesPat.one", "rcasesPat.alts",
  "rcasesPatMed", "rcasesPatLo", "rcasesPat.paren", "rcasesPat.type",
  "obtain", "case", "next", "renameI", "rename_i", "have", "let", "show", "change",
  "subst", "revert", "generalize", "clear", "specialize",
  "allGoals", "anyGoals", "first", "repeat", "repeat'", "try", "focus", "done",
  "tacticSeq1Indented", "tacticSeq", "seq1", "seq", "seqFocus", "orElse", "andThen", "parens",
  "haveLet", "haveDecl", "haveIdDecl", "havePatDecl", "letIdDecl", "letPatDecl"
]

partial def checkSyntax (stx : Syntax) : Except String Unit := do
  match stx with
  | .node _ kind args =>
    let ks := kind.toString
    if ks.startsWith "Lean.Parser.Tactic." then
      let localName := ks.drop "Lean.Parser.Tactic.".length
      unless safeTacticKinds.contains localName do
        throw ("Tactic syntax outside the published proof language: " ++ ks)
      -- Even a pure-looking config can invoke the native expression evaluator.
      if localName == "optConfig" && !args.isEmpty then
        if args.any (fun a => !a.isMissing && a.getNumArgs != 0) then
          throw "Custom tactic configuration is not allowed"
    if ks == "Lean.Parser.Term.set_option" || ks == "Lean.Parser.Term.run" ||
        ks == "Lean.Parser.Term.runMeta" || ks == "Lean.Parser.Term.eval" ||
        ks == "Lean.byElab" || ks == "Lean.Parser.Term.unsafe" || ks == "Lean.includeStr" then
      throw "Term-level metaprogram execution/options/external input are not allowed"
    for a in args do checkSyntax a
  | _ => pure ()

partial def syntaxKinds (s : Syntax) : Array String :=
  match s with
  | .node _ k args => #[k.toString] ++ (args.flatMap syntaxKinds)
  | _ => #[]

def goals : Array (String × Name) := #[
  ("step_balance", `NRB.Goals.step_balance),
  ("zero_input_active", `NRB.Goals.zero_input_active),
  ("trace_balance", `NRB.Goals.trace_balance),
  ("restart", `NRB.Goals.restart),
  ("prefix_admissible", `NRB.Goals.prefix_admissible),
  ("collected_bound", `NRB.Goals.collected_bound)
]

def failRecord (id msg : String) : Json := Json.mkObj [
  ("ok", toJson false), ("error", toJson "ProofRejected"), ("detail", toJson msg),
  ("goal", toJson id)
]

unsafe def checkProof (env : Environment) (id : String) (goal : Name) (proof : String) : IO Json := do
  try
    let stx ← IO.ofExcept (Parser.runParserCategory env `term proof)
    -- Print is disabled for normal evaluation; helpful when auditing syntax.
    if (← IO.getEnv "NRB_LEAN_AST") == some "1" then
      IO.eprintln (toJson ((syntaxKinds stx).toList.eraseDups)).compress
    IO.ofExcept (checkSyntax stx)
    let opts := ({} : Options).setBool `Elab.async false |>.setBool `debug.skipKernelTC false |>.setNat `maxHeartbeats 2000000
    let target := mkConst goal
    let name := Name.str `NRB.Checked id
    let action : CoreM (Array Name × String) := MetaM.run' <| Term.TermElabM.run' do
      let value ← Term.elabTermEnsuringType stx (some target)
      Term.synthesizeSyntheticMVarsNoPostponing
      let value ← instantiateMVars value
      unless !value.hasMVar && !value.hasFVar do throwError "Unclosed proof"
      -- Synchronous kernel checking is forced after elaboration.
      withOptions (fun _ => opts) do
        addDecl <| Declaration.thmDecl { name := name, levelParams := [], type := target, value := value }
      let some info := (← getEnv).checked.get.find? name | throwError "Missing kernel declaration"
      unless info.type == target do throwError "Target type changed"
      let axs ← collectAxioms name
      let statement ← ppExpr (← whnf target)
      return (axs, toString statement)
    let ctx : Core.Context := {
      fileName := "candidate-proof"
      fileMap := FileMap.ofString proof
      options := opts
      currNamespace := `NRB
      openDecls := [.simple `NRB []]
    }
    -- Every goal starts from the identical trusted environment. No failed or
    -- successful previous candidate declaration is available to another goal.
    let ((axs, statement), state) ← action.toIO ctx { env := env }
    if state.messages.hasErrors then
      return failRecord id "Elaboration produced errors"
    let allowed : Array Name := #[`propext, `Classical.choice, `Quot.sound]
    if axs.any (fun ax => !allowed.contains ax) then
      return failRecord id ("Forbidden transitive axiom dependency: " ++ String.intercalate ", " (axs.toList.map Name.toString))
    return Json.mkObj [
      ("ok", toJson true),
      ("value", Json.mkObj [
        ("goal", toJson id), ("kernel_checked", toJson true),
        ("target_verified", toJson true), ("axioms", toJson (axs.map Name.toString)),
        ("statement", toJson statement)
      ])
    ]
  catch err =>
    return failRecord id err.toString

unsafe def main (args : List String) : IO UInt32 := do
  initSearchPath (← findSysroot)
  enableInitializersExecution
  let env ← importModules (loadExts := true) #[{ module := `NRBPrelude }] {} 0
  let data ← IO.ofExcept (Json.parse (← IO.FS.readFile (args[0]!)))
  let mut records : Array Json := #[]
  for (id, goal) in goals do
    match data.getObjValAs? String id with
    | .error msg => records := records.push (failRecord id msg)
    | .ok proof => records := records.push (← checkProof env id goal proof)
  IO.println ("NRB_L01_RESULTS=" ++ (toJson records).compress)
  return 0
