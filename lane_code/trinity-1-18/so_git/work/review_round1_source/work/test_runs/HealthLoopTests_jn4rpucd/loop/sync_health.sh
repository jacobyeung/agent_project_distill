if [ ! -e "$LCS_S/first_check" ]; then
  echo first > "$LCS_S/first_check"; exit 137
fi
echo second > "$LCS_S/second_check"
