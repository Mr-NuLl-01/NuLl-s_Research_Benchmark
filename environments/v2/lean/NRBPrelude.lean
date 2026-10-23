import Lean

namespace NRB

structure State where
  active : Nat
  collected : Nat
  lost : Nat
  deriving Repr, DecidableEq

structure Event where
  injected : Nat
  collect : Nat
  lose : Nat
  deriving Repr, DecidableEq

def total (s : State) : Nat := s.active + s.collected + s.lost

def admissible (s : State) (e : Event) : Prop := e.collect + e.lose ≤ s.active + e.injected

def step (s : State) (e : Event) : State :=
  ⟨s.active + e.injected - (e.collect + e.lose),
   s.collected + e.collect, s.lost + e.lose⟩

def run : State → List Event → State
  | s, [] => s
  | s, e :: es => run (step s e) es

def injected : List Event → Nat
  | [] => 0
  | e :: es => e.injected + injected es

def admissibleTrace : State → List Event → Prop
  | _, [] => True
  | s, e :: es => admissible s e ∧ admissibleTrace (step s e) es

namespace Goals

def step_balance : Prop := ∀ (s : State) (e : Event),
  admissible s e → total (step s e) = total s + e.injected

def zero_input_active : Prop := ∀ (s : State) (e : Event),
  e.injected = 0 → (step s e).active ≤ s.active

def trace_balance : Prop := ∀ (s : State) (es : List Event),
  admissibleTrace s es → total (run s es) = total s + injected es

def restart : Prop := ∀ (s : State) (xs ys : List Event),
  run s (xs ++ ys) = run (run s xs) ys

def prefix_admissible : Prop := ∀ (s : State) (xs ys : List Event),
  admissibleTrace s (xs ++ ys) → admissibleTrace s xs

def collected_bound : Prop := ∀ (s : State) (es : List Event),
  admissibleTrace s es → (run s es).collected ≤ total s + injected es

end Goals
end NRB
