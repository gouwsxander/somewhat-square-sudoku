for d in 1 3 4 6 7 8 9; do
    python enumerate-by-divisor.py $d > output_$d.log 2>&1 &
    echo "Started process for digit $d with PID $!"
done
