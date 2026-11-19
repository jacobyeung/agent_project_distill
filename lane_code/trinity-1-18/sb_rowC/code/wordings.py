TEMPLATES = [
"Count the separate objects in the '{a}' and '{b}' categories. For '{a}' relative to '{b}', which choice describes the result?",
"Consider the room's '{a}' objects as one group and its '{b}' objects as another. Which comparison describes the size of the first group?",
"Tally distinct instances of '{a}' and then distinct instances of '{b}' across the video. How does the first tally compare with the second?",
"Use a separate tally for each category: '{a}' followed by '{b}'. Which option correctly compares the first category's total to the second category's total?",
"Inspect the room for objects belonging to '{a}' and '{b}'. After counting each object once, choose the relation of the '{a}' count to the '{b}' count.",
"The categories to compare are '{a}' and '{b}', in that order. Which answer describes the number of distinct objects in the first category relative to the second?",
"Keep track of distinct '{a}' objects while viewing the room, and do the same for '{b}'. Select the comparison that places the '{a}' tally against the '{b}' tally.",
"Make independent counts for '{a}' and '{b}' using the video. Which option states how the total for '{a}' compares with the total for '{b}'?",
"For a count comparison, take '{a}' as the first category and '{b}' as the second. What relation between their numbers of instances does the room show?",
"Look through the room views and count each distinct object in '{a}' and in '{b}'. Compared with the second category, how many instances does the first category have: more, fewer, or an equal number?",
"Assess the numbers of objects belonging to '{a}' and '{b}' without counting repeat views twice. Which choice gives the comparison for '{a}' against '{b}'?",
"Start with a count of the room's distinct '{a}' objects, then count its distinct '{b}' objects. Select the option that relates the first count to the second.",
"Treat '{a}' and '{b}' as separate categories when counting objects in the scene. Which answer fits the number in '{a}' relative to the number in '{b}'?",
"Review the video to establish a total for '{a}' and a total for '{b}'. How should the '{a}' total be classified when compared with the '{b}' total?",
"Compare category totals after identifying the distinct objects in the room: '{a}' first, '{b}' second. Which choice describes the first total in relation to the second?",
"There are separate object categories named '{a}' and '{b}' to tally in these views. Choose the count relationship with '{a}' as the category being compared and '{b}' as the reference.",
"Determine how many separate objects belong to '{a}' and how many belong to '{b}'. Using those totals, choose the comparison of '{a}' with '{b}'.",
"Use the room video to compare the populations of '{a}' objects and '{b}' objects. Which option describes the first population relative to the second after repeated views are counted only once?",
"For the objects in categories '{a}' and '{b}', compare distinct-instance totals across the room. Read each answer choice as describing '{a}' relative to '{b}' and select the correct one.",
"Work out separate object totals for '{a}' and '{b}' from the scene. With the '{b}' total as the reference, which answer describes the '{a}' total?",
]
# Per-template cells: 90 first-category wins, 90 second-category wins, 20 ties.
BUCKET_QUOTAS={'2':28,'3':18,'4':12,'5':10,'6':8,'7':4,'8':4,'9':3,'10':3}
