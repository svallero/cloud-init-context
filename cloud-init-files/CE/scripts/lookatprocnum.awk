{
processes[$1]++;
} 
END {
printf "\n";
	for (i in processes) {
		 if (processes[i] > 100) {
	 		print processes[i],i;
	 	 }
  	}
}
