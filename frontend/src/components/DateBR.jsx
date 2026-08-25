function DateBR({iso}){
    const date = new Date(iso+'T00:00:00');
    const formatted = date.toLocaleDateString('pt-BR');
    return <span>{formatted}</span>;
}
export default DateBR;