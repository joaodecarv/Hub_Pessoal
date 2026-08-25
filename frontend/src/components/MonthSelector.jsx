const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function MonthSelector({ year, month, onChange }){
    function shift(delta){
        let m = month + delta
        let y = year
        if (m < 1){ m = 12; y -= 1 }
        if (m > 12){ m = 1; y += 1 }
        onChange(y, m)
    }

    return (
        <div className="month-select">
            <button onClick={() => shift(-1)} aria-label="Previous month">‹</button>
            <span className="ms-label">{MONTHS[month - 1]} / {year}</span>
            <button onClick={() => shift(1)} aria-label="Next month">›</button>
        </div>
    )
}

export default MonthSelector
