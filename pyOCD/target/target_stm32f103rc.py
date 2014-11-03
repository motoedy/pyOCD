"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2006-2013 ARM Limited

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from cortex_m import CortexM, DHCSR, DBGKEY, C_DEBUGEN, C_MASKINTS, C_STEP, DEMCR, VC_CORERESET, NVIC_AIRCR, NVIC_AIRCR_VECTKEY, NVIC_AIRCR_SYSRESETREQ
from pyOCD.target.target import TARGET_RUNNING, TARGET_HALTED
import logging


class STM32F103RC(CortexM):

    memoryMapXML =  """<?xml version="1.0"?>
<!DOCTYPE memory-map PUBLIC "+//IDN gnu.org//DTD GDB Memory Map V1.0//EN" "http://sourceware.org/gdb/gdb-memory-map.dtd">
<memory-map>
    <memory type="flash" start="0x08000000" length="0x80000"> <property name="blocksize">0x800</property></memory>
    <memory type="ram" start="0x20000000" length="0x10000"> </memory>
</memory-map>
"""
    
    def __init__(self, transport):
        super(STM32F103RC, self).__init__(transport)
        self.auto_increment_page_size = 0x800

    def step(self):
        """
        perform an instruction level step
        Without this GDB client can't step through the code.
        """
        if self.getState() != TARGET_HALTED:
            logging.debug('cannot step: target not halted')
            return
        if self.maybeSkipBreakpoint() is None:
            self.writeMemory(DHCSR, DBGKEY | C_DEBUGEN | C_MASKINTS | C_STEP)
        return

    def reset(self):
        """
        reset a core. After a call to this function, the core
        is running
        """
        # For some reason hardware reset prevent normal operation.
        self.resetStopResume()

    def resetStopResume(self):
        """
        reset a core. After a call to this function, the core
        is running
        """
        self.resetStopOnReset()
        self.resume()

    def resetStopOnReset(self):
        """
        perform a reset and stop the core on the reset handler
        """
        # read address of reset handler
        reset_handler = self.readMemory(4)

        # halt on reset the target
        self.halt()
        # set a breakpoint to the reset handler and reset the target
        self.setBreakpoint(reset_handler)

        #Soft Reset will keep stm32 in debug mode
        self.writeMemory(DEMCR, VC_CORERESET)
        self.writeMemory(NVIC_AIRCR, NVIC_AIRCR_VECTKEY | NVIC_AIRCR_SYSRESETREQ)
        
        # wait until the bp is reached
        while (self.getState() == TARGET_RUNNING):
            pass
        
        # remove the breakpoint
        self.removeBreakpoint(reset_handler)

