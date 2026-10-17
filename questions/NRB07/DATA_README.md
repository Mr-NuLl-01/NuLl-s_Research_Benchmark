# Generated repeated-machine exercise

records.csv and predictions.csv are synthetic benchmark inputs, not observations
from actual machines or the results of training an actual classifier. Every
machine supplies repeated readings of the same underlying mechanical condition.
The proposed row-level split is deliberately unreliable. Machine identity is
the independent grouping unit. Labels and repeat counts are intentionally
imbalanced. The split rule in protocol.json is fixed before inspecting predictions.

Join predictions to records by row_id, never by line number. File orders differ.
The supplied predictions are frozen candidate predictions; do not train,
threshold-tune, or alter them. Apply the declared validation metric to select
the model once. Test predictions are only for evaluating that selected model.

For uncertainty use the provided exact cluster bootstrap index plan. It removes
random-generator/version differences between implementations. Resampling rows
independently or discarding repeated sampled machine IDs changes the estimand.
The number of readings is not the number of independent machines. A bootstrap
percentile interval in this small synthetic exercise is not a guarantee of
population coverage or performance on a different manufacturing environment.
